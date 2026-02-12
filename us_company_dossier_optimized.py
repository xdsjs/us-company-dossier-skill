#!/usr/bin/env python3
"""
US Company Dossier Skill (Optimized Version)
Builds comprehensive company research dossiers from SEC EDGAR and IR materials.
This optimized version organizes files by form type for easier navigation.
"""

import os
import json
import hashlib
import time
import re
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import shutil
from urllib.parse import urljoin, urlparse
import html2text
from dataclasses import dataclass, asdict
from enum import Enum

# Load .env from project root when module is imported
def _load_dotenv():
    _skill_dir = Path(__file__).parent
    for base in [_skill_dir.parent.parent, Path(os.getcwd())]:
        env_path = base / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                m = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
                if m and not line.strip().startswith("#"):
                    key, val = m.group(1), m.group(2).strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val
            break

_load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NormalizeLevel(Enum):
    NONE = "none"
    LIGHT = "light"
    DEEP = "deep"

@dataclass
class Artifact:
    id: str
    source: str  # "sec" or "ir"
    type: str    # "filing", "exhibit", "xbrl", "press", "presentation", "other"
    form: Optional[str] = None
    period: Optional[str] = None
    filed_at: Optional[str] = None
    url: str = ""
    local_path: str = ""
    content_type: str = ""
    size_bytes: int = 0
    sha256: str = ""
    downloaded_at: str = ""
    parse_status: str = "pending"  # "pending", "success", "failed", "links_only"
    parse_error: Optional[str] = None
    versioning: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class CompanyInfo:
    ticker: str
    company_name: Optional[str] = None
    cik: Optional[str] = None
    exchange: Optional[str] = None
    cusip: Optional[str] = None

@dataclass
class RunInfo:
    run_id: str
    started_at: str
    ended_at: str
    status: str
    version: str = "1.0"

@dataclass
class ConfigSnapshot:
    years: int
    forms: List[str]
    include_ir: bool
    max_filings_per_form: int
    force_rebuild: bool
    normalize_level: str
    fetch_mode: str
    sec_user_agent: str
    sec_rps_limit: int
    domain_allowlist: List[str]
    ir_base_url_map: Dict[str, str]

class USCCompanyDossier:
    def __init__(self, workspace_root: str = None, dossier_root: str = None):
        # Dossier output: explicit param > DOSSIER_ROOT env > workspace/dossiers
        if dossier_root:
            self.dossier_root = dossier_root
        elif os.getenv("DOSSIER_ROOT"):
            self.dossier_root = os.getenv("DOSSIER_ROOT")
        else:
            # Default to the OpenClaw workspace root if not specified
            if workspace_root is None:
                workspace_root = (
                    os.getenv("WORKSPACE_ROOT") or
                    os.getenv("OPENCLAW_WORKSPACE") or
                    "/Users/jss/clawd"
                )
                if not os.path.exists(workspace_root):
                    workspace_root = os.getcwd()
            self.dossier_root = os.path.join(workspace_root, "dossiers")
        self.workspace_root = os.path.dirname(self.dossier_root)
        self.sec_user_agent = os.getenv("SEC_USER_AGENT", "OpenClawResearchBot/1.0 (research@openclaw.ai)")
        self.sec_rps_limit = int(os.getenv("SEC_RPS_LIMIT", "3"))
        self.domain_allowlist = os.getenv("DOMAIN_ALLOWLIST", "").split(",") if os.getenv("DOMAIN_ALLOWLIST") else []
        self.ir_base_url_map = {}
        if os.getenv("IR_BASE_URL_MAP"):
            try:
                self.ir_base_url_map = json.loads(os.getenv("IR_BASE_URL_MAP"))
            except json.JSONDecodeError:
                logger.warning("Invalid IR_BASE_URL_MAP, using empty dict")
        
        # Load ticker to CIK mapping
        self.ticker_cik_map = {}

    def build_dossier(self, ticker: str, years: int = 3, forms: List[str] = None, 
                     include_ir: bool = True, max_filings_per_form: int = 50,
                     force_rebuild: bool = False, normalize_level: str = "light",
                     fetch_mode: str = "http", download_mode: str = "links_only") -> Dict:
        """Build a comprehensive company dossier.
        
        Args:
            download_mode: "links_only" (default) generates SEC links without downloading,
                          "full" downloads complete files for offline analysis.
        """
        if forms is None:
            forms = ["10-K", "10-Q", "8-K", "DEF 14A", "4"]
        
        # Create dossier directory
        dossier_path = os.path.join(self.dossier_root, ticker)
        os.makedirs(dossier_path, exist_ok=True)
        
        # Initialize manifest
        manifest = {
            "company": {"ticker": ticker},
            "run_info": {
                "run_id": f"run_{int(time.time())}",
                "started_at": datetime.now().isoformat(),
                "ended_at": "",
                "status": "running",
                "version": "1.0"
            },
            "config_snapshot": {
                "years": years,
                "forms": forms,
                "include_ir": include_ir,
                "max_filings_per_form": max_filings_per_form,
                "force_rebuild": force_rebuild,
                "normalize_level": normalize_level,
                "fetch_mode": fetch_mode,
                "sec_user_agent": self.sec_user_agent,
                "sec_rps_limit": self.sec_rps_limit,
                "domain_allowlist": self.domain_allowlist,
                "ir_base_url_map": self.ir_base_url_map
            },
            "artifacts": []
        }
        
        manifest_path = os.path.join(dossier_path, "manifest.json")
        self._save_manifest(manifest, manifest_path)
        
        # Get company info (CIK)
        company_info = self._get_company_info(ticker)
        manifest["company"].update(asdict(company_info))
        
        # Fetch and download SEC filings
        filings = self._fetch_sec_filings(company_info.cik, forms, years, max_filings_per_form)
        sec_artifacts = self._download_sec_filings_optimized(ticker, company_info.cik, filings, dossier_path, force_rebuild, download_mode)
        
        # Download XBRL facts
        xbrl_artifacts = self._download_xbrl_facts(company_info.cik, dossier_path, force_rebuild)
        
        # Fetch IR materials
        ir_artifacts = []
        if include_ir:
            ir_artifacts = self._fetch_ir_materials(ticker, dossier_path, force_rebuild, fetch_mode)
        
        all_artifacts = sec_artifacts + xbrl_artifacts + ir_artifacts
        manifest["artifacts"] = [asdict(artifact) for artifact in all_artifacts]
        
        # Update summary
        summary = {
            "downloaded_count": 0,
            "parsed_success": 0,
            "parsed_failed": 0,
            "skipped_cached": 0,
            "latest_filed_at": None
        }
        self._update_summary_from_artifacts(all_artifacts, summary)
        
        # Normalize and index (skip in links_only mode)
        if normalize_level != "none" and download_mode != "links_only":
            normalized_artifacts = self._normalize_and_index(dossier_path, manifest["artifacts"], normalize_level)
            # Update artifacts with normalized status
            for i, norm_artifact in enumerate(normalized_artifacts):
                if i < len(manifest["artifacts"]):
                    manifest["artifacts"][i].update(asdict(norm_artifact))
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(manifest, years)
        
        # Finalize manifest
        manifest["run_info"]["ended_at"] = datetime.now().isoformat()
        manifest["run_info"]["status"] = "completed"
        self._save_manifest(manifest, manifest_path)
        
        return {
            "dossier_path": dossier_path,
            "summary": summary,
            "errors": [],
            "quality_metrics": quality_metrics
        }

    def _get_company_info(self, ticker: str) -> CompanyInfo:
        """Get company information including CIK."""
        # Load ticker to CIK mapping if not already loaded
        if not self.ticker_cik_map:
            ticker_cik_path = os.path.join(os.path.dirname(__file__), "ticker_cik_map.json")
            if os.path.exists(ticker_cik_path):
                with open(ticker_cik_path, "r") as f:
                    self.ticker_cik_map = json.load(f)
        
        cik = self.ticker_cik_map.get(ticker.upper())
        if not cik:
            # Fallback: try to get from SEC API
            try:
                headers = {"User-Agent": self.sec_user_agent}
                response = requests.get(
                    f"https://www.sec.gov/files/company_tickers.json",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                tickers_data = response.json()
                
                for entry in tickers_data.values():
                    if entry["ticker"].upper() == ticker.upper():
                        cik = str(entry["cik_str"]).zfill(10)
                        break
                
                if cik:
                    # Update mapping
                    self.ticker_cik_map[ticker.upper()] = cik
                    with open(os.path.join(os.path.dirname(__file__), "ticker_cik_map.json"), "w") as f:
                        json.dump(self.ticker_cik_map, f, indent=2)
                        
            except Exception as e:
                logger.warning(f"Could not fetch CIK for {ticker}: {e}")
                cik = None
        
        return CompanyInfo(ticker=ticker, cik=cik)

    def _fetch_sec_filings(self, cik: str, forms: List[str], years: int, max_filings_per_form: int) -> List[Dict]:
        """Fetch SEC filing metadata."""
        if not cik:
            return []
        
        try:
            headers = {"User-Agent": self.sec_user_agent}
            submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            
            response = requests.get(submissions_url, headers=headers, timeout=30)
            response.raise_for_status()
            submissions = response.json()
            
            filings = submissions.get("filings", {}).get("recent", {})
            if not filings:
                # Fallback structure
                filings = submissions
            
            # Filter by forms and years
            cutoff_date = datetime.now() - timedelta(days=years*365)
            filtered_filings = []
            form_counts = {form: 0 for form in forms}  # Track count per form type
            
            for i, form in enumerate(filings.get("form", [])):
                if form not in forms:
                    continue
                
                # Check if we've already reached the limit for this form type
                if form_counts[form] >= max_filings_per_form:
                    continue
                
                filed_date = filings.get("filingDate", [])[i]
                filed_dt = datetime.strptime(filed_date, "%Y-%m-%d")
                if filed_dt < cutoff_date:
                    continue
                
                filing = {
                    "form": form,
                    "filed_date": filed_date,
                    "accession_number": filings.get("accessionNumber", [])[i],
                    "primary_document": filings.get("primaryDocument", [])[i],
                    "description": filings.get("description", [])[i] if i < len(filings.get("description", [])) else ""
                }
                filtered_filings.append(filing)
                form_counts[form] += 1
            
            return filtered_filings
            
        except Exception as e:
            logger.error(f"Error fetching SEC filings for CIK {cik}: {e}")
            return []

    def _download_sec_filings_optimized(self, ticker: str, cik: str, filings: List[Dict], dossier_path: str, force_rebuild: bool, download_mode: str = "links_only") -> List[Artifact]:
        """Download SEC filings and organize by form type.
        
        Args:
            download_mode: "links_only" (default) or "full"
        """
        artifacts = []
        raw_sec_path = os.path.join(dossier_path, "raw", "sec")
        
        # Define form type categories for organization
        form_categories = {
            "10-K": "financial_reports",
            "10-Q": "financial_reports", 
            "20-F": "financial_reports",
            "40-F": "financial_reports",
            "8-K": "material_events",
            "6-K": "material_events",
            "DEF 14A": "proxy_statements",
            "4": "insider_transactions",
            "3": "insider_transactions",
            "5": "insider_transactions",
            "S-1": "registration_statements",
            "S-3": "registration_statements",
            "S-4": "registration_statements",
            "S-8": "registration_statements",
            "13F-HR": "institutional_holdings",
            "13F-NT": "institutional_holdings",
            "N-CSR": "fund_reports",
            "N-CSRS": "fund_reports",
            "N-Q": "fund_reports"
        }
        
        headers = {"User-Agent": self.sec_user_agent}
        
        for filing in filings:
            try:
                # Determine category and create appropriate directory
                form_type = filing["form"]
                category = form_categories.get(form_type, "other_filings")
                category_path = os.path.join(raw_sec_path, category)
                os.makedirs(category_path, exist_ok=True)
                
                # Download primary document
                accession_clean = filing["accession_number"].replace("-", "")
                primary_doc = filing["primary_document"]
                primary_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}"
                
                file_ext = os.path.splitext(primary_doc)[1] or ".html"
                # Include accession number to avoid filename conflicts
                local_filename = f"{filing['filed_date']}_{form_type}_{accession_clean}{file_ext}"
                local_path = os.path.join(category_path, local_filename)
                
                artifact_id = f"sec_filing_{filing['accession_number']}_{form_type}"
                
                # Links-only mode: generate metadata without downloading
                if download_mode == "links_only":
                    viewer_url = self._generate_online_viewer_url(cik, filing["accession_number"], primary_doc)
                    artifact = Artifact(
                        id=artifact_id,
                        source="sec",
                        type="filing",
                        form=form_type,
                        filed_at=filing["filed_date"],
                        url=primary_url,
                        local_path="",  # No local file in links-only mode
                        content_type=f"text/{file_ext.lstrip('.')}",
                        size_bytes=0,
                        sha256="",
                        downloaded_at=datetime.now().isoformat(),
                        parse_status="links_only",
                        metadata={"viewer_url": viewer_url, "raw_url": primary_url}
                    )
                    artifacts.append(artifact)
                    continue
                
                # Check if already downloaded and hash matches
                if not force_rebuild and os.path.exists(local_path):
                    existing_hash = self._calculate_file_hash(local_path)
                    artifact = Artifact(
                        id=artifact_id,
                        source="sec",
                        type="filing",
                        form=form_type,
                        filed_at=filing["filed_date"],
                        url=primary_url,
                        local_path=local_path,
                        content_type=f"text/{file_ext.lstrip('.')}",
                        size_bytes=os.path.getsize(local_path),
                        sha256=existing_hash,
                        downloaded_at=datetime.fromtimestamp(os.path.getmtime(local_path)).isoformat(),
                        parse_status="pending"
                    )
                    artifacts.append(artifact)
                    continue
                
                # Download file
                response = requests.get(primary_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                with open(local_path, "wb") as f:
                    f.write(response.content)
                
                file_hash = self._calculate_file_hash(local_path)
                downloaded_at = datetime.now().isoformat()
                
                artifact = Artifact(
                    id=artifact_id,
                    source="sec",
                    type="filing",
                    form=form_type,
                    filed_at=filing["filed_date"],
                    url=primary_url,
                    local_path=local_path,
                    content_type=response.headers.get("content-type", f"text/{file_ext.lstrip('.')}"),
                    size_bytes=len(response.content),
                    sha256=file_hash,
                    downloaded_at=downloaded_at,
                    parse_status="pending"
                )
                artifacts.append(artifact)
                
                # TODO: Download key exhibits (this is simplified)
                # In a full implementation, we'd parse the filing to find exhibits
                
            except Exception as e:
                logger.error(f"Error downloading filing {filing['accession_number']}: {e}")
                artifact = Artifact(
                    id=f"sec_filing_{filing['accession_number']}_{form_type}",
                    source="sec",
                    type="filing",
                    form=form_type,
                    filed_at=filing["filed_date"],
                    url="",
                    local_path="",
                    parse_status="failed",
                    parse_error=str(e)
                )
                artifacts.append(artifact)
        
        return artifacts

    def _download_xbrl_facts(self, cik: str, dossier_path: str, force_rebuild: bool) -> List[Artifact]:
        """Download XBRL company facts."""
        artifacts = []
        xbrl_path = os.path.join(dossier_path, "raw", "sec", "structured_data", "xbrl")
        os.makedirs(xbrl_path, exist_ok=True)
        
        companyfacts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        headers = {"User-Agent": self.sec_user_agent}
        
        try:
            local_path = os.path.join(xbrl_path, f"{cik}_companyfacts.json")
            
            if not force_rebuild and os.path.exists(local_path):
                existing_hash = self._calculate_file_hash(local_path)
                artifact = Artifact(
                    id=f"sec_xbrl_{cik}_companyfacts",
                    source="sec",
                    type="xbrl",
                    url=companyfacts_url,
                    local_path=local_path,
                    content_type="application/json",
                    size_bytes=os.path.getsize(local_path),
                    sha256=existing_hash,
                    downloaded_at=datetime.fromtimestamp(os.path.getmtime(local_path)).isoformat(),
                    parse_status="pending"
                )
                artifacts.append(artifact)
                return artifacts
            
            response = requests.get(companyfacts_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(local_path, "w") as f:
                json.dump(response.json(), f, indent=2)
            
            file_hash = self._calculate_file_hash(local_path)
            downloaded_at = datetime.now().isoformat()
            
            artifact = Artifact(
                id=f"sec_xbrl_{cik}_companyfacts",
                source="sec",
                type="xbrl",
                url=companyfacts_url,
                local_path=local_path,
                content_type="application/json",
                size_bytes=len(response.content),
                sha256=file_hash,
                downloaded_at=downloaded_at,
                parse_status="pending"
            )
            artifacts.append(artifact)
            
        except Exception as e:
            logger.error(f"Error downloading XBRL facts for CIK {cik}: {e}")
            artifact = Artifact(
                id=f"sec_xbrl_{cik}_companyfacts",
                source="sec",
                type="xbrl",
                url=companyfacts_url,
                parse_status="failed",
                parse_error=str(e)
            )
            artifacts.append(artifact)
        
        return artifacts

    def _fetch_ir_materials(self, ticker: str, dossier_path: str, force_rebuild: bool, fetch_mode: str) -> List[Artifact]:
        """Fetch IR materials (press releases, presentations)."""
        artifacts = []
        
        # Get IR base URL
        ir_base_url = self.ir_base_url_map.get(ticker)
        if not ir_base_url:
            # Try common patterns
            ir_base_url = f"https://investors.{ticker.lower()}.com"
        
        if not ir_base_url:
            return artifacts
        
        # Check domain allowlist
        if self.domain_allowlist and urlparse(ir_base_url).netloc not in self.domain_allowlist:
            logger.warning(f"IR domain {urlparse(ir_base_url).netloc} not in allowlist")
            return artifacts
        
        try:
            press_path = os.path.join(dossier_path, "raw", "ir", "press_releases")
            presentations_path = os.path.join(dossier_path, "raw", "ir", "presentations")
            earnings_path = os.path.join(dossier_path, "raw", "ir", "earnings")
            os.makedirs(press_path, exist_ok=True)
            os.makedirs(presentations_path, exist_ok=True)
            os.makedirs(earnings_path, exist_ok=True)
            
            # This is a simplified implementation
            # In reality, you'd need to parse the IR site structure
            # For demo purposes, we'll just show the structure
            
            # TODO: Implement actual IR scraping logic
            # This would involve:
            # 1. Fetching press release list page
            # 2. Parsing links to individual press releases
            # 3. Downloading HTML content
            # 4. Similarly for presentations (PDF downloads)
            
            logger.info(f"IR fetching not fully implemented in demo. Would fetch from {ir_base_url}")
            
        except Exception as e:
            logger.error(f"Error fetching IR materials for {ticker}: {e}")
        
        return artifacts

    def _normalize_and_index(self, dossier_path: str, artifacts: List[Dict], normalize_level: str) -> List[Artifact]:
        """Normalize artifacts and create index."""
        normalized_path = os.path.join(dossier_path, "normalized")
        index_path = os.path.join(dossier_path, "index")
        os.makedirs(normalized_path, exist_ok=True)
        os.makedirs(index_path, exist_ok=True)
        
        normalized_artifacts = []
        documents_jsonl_path = os.path.join(index_path, "documents.jsonl")
        
        with open(documents_jsonl_path, "w") as index_file:
            for artifact_dict in artifacts:
                artifact = Artifact(**artifact_dict)
                if artifact.parse_status == "failed":
                    normalized_artifacts.append(artifact)
                    continue
                
                try:
                    normalized_artifact = self._normalize_artifact(artifact, normalized_path, normalize_level)
                    normalized_artifacts.append(normalized_artifact)
                    
                    # Create index entries
                    if normalize_level == "light" and artifact.local_path and os.path.exists(artifact.local_path):
                        chunks = self._chunk_document(artifact, normalized_artifact, normalized_path)
                        for chunk in chunks:
                            index_file.write(json.dumps(chunk) + "\n")
                
                except Exception as e:
                    logger.error(f"Error normalizing artifact {artifact.id}: {e}")
                    artifact.parse_status = "failed"
                    artifact.parse_error = str(e)
                    normalized_artifacts.append(artifact)
        
        return normalized_artifacts

    def _normalize_artifact(self, artifact: Artifact, normalized_path: str, normalize_level: str) -> Artifact:
        """Normalize a single artifact."""
        if not artifact.local_path or not os.path.exists(artifact.local_path):
            artifact.parse_status = "failed"
            artifact.parse_error = "Local path does not exist"
            return artifact
        
        file_ext = os.path.splitext(artifact.local_path)[1].lower()
        
        # Preserve the same directory structure in normalized folder
        relative_path = os.path.relpath(os.path.dirname(artifact.local_path), 
                                      os.path.join(os.path.dirname(artifact.local_path), '..', '..'))
        normalized_dir = os.path.join(normalized_path, relative_path)
        os.makedirs(normalized_dir, exist_ok=True)
        
        normalized_md_path = os.path.join(normalized_dir, f"{artifact.id}.md")
        normalized_json_path = os.path.join(normalized_dir, f"{artifact.id}.json")
        
        try:
            if file_ext in ['.html', '.htm']:
                # Convert HTML to Markdown
                with open(artifact.local_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                h.body_width = 0
                markdown_content = h.handle(html_content)
                
                with open(normalized_md_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                # Create metadata JSON
                metadata = {
                    "artifact_id": artifact.id,
                    "source": artifact.source,
                    "type": artifact.type,
                    "original_path": artifact.local_path,
                    "normalized_at": datetime.now().isoformat(),
                    "word_count": len(markdown_content.split())
                }
                with open(normalized_json_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                artifact.parse_status = "success"
                
            elif file_ext == '.pdf':
                # PDF handling would require pdfplumber or similar
                # For demo, mark as failed
                artifact.parse_status = "failed"
                artifact.parse_error = "PDF parsing not implemented in demo"
                
            elif file_ext == '.txt':
                # Plain text - copy as-is
                shutil.copy2(artifact.local_path, normalized_md_path)
                metadata = {
                    "artifact_id": artifact.id,
                    "source": artifact.source,
                    "type": artifact.type,
                    "original_path": artifact.local_path,
                    "normalized_at": datetime.now().isoformat()
                }
                with open(normalized_json_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                artifact.parse_status = "success"
                
            elif file_ext == '.json':
                # JSON files - pretty print
                with open(artifact.local_path, 'r') as f:
                    json_data = json.load(f)
                with open(normalized_md_path, 'w') as f:
                    f.write(f"```json\n{json.dumps(json_data, indent=2)}\n```")
                metadata = {
                    "artifact_id": artifact.id,
                    "source": artifact.source,
                    "type": artifact.type,
                    "original_path": artifact.local_path,
                    "normalized_at": datetime.now().isoformat()
                }
                with open(normalized_json_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                artifact.parse_status = "success"
            
            else:
                artifact.parse_status = "failed"
                artifact.parse_error = f"Unsupported file type: {file_ext}"
        
        except Exception as e:
            artifact.parse_status = "failed"
            artifact.parse_error = str(e)
        
        return artifact

    def _chunk_document(self, original_artifact: Artifact, normalized_artifact: Artifact, normalized_path: str) -> List[Dict]:
        """Chunk a normalized document for indexing."""
        if normalized_artifact.parse_status != "success":
            return []
        
        # Build correct path to normalized markdown file
        relative_path = os.path.relpath(os.path.dirname(original_artifact.local_path), 
                                      os.path.join(os.path.dirname(original_artifact.local_path), '..', '..'))
        normalized_dir = os.path.join(normalized_path, relative_path)
        normalized_md_path = os.path.join(normalized_dir, f"{normalized_artifact.id}.md")
        
        if not os.path.exists(normalized_md_path):
            return []
        
        try:
            with open(normalized_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple chunking by paragraphs and headings
            lines = content.split('\n')
            chunks = []
            current_chunk = []
            current_section = []
            
            for line in lines:
                if line.strip().startswith('#'):
                    # New section heading
                    if current_chunk:
                        chunk_text = '\n'.join(current_chunk)
                        if len(chunk_text.strip()) > 50:  # Minimum meaningful content
                            chunks.append({
                                "artifact_id": original_artifact.id,
                                "source_url": original_artifact.url,
                                "section_path": current_section.copy(),
                                "chunk_index": len(chunks),
                                "text": chunk_text,  # Use "text" for consistency with README
                                "word_count": len(chunk_text.split())
                            })
                        current_chunk = []
                    current_section = [line.strip()]
                else:
                    current_chunk.append(line)
            
            # Add final chunk
            if current_chunk:
                chunk_text = '\n'.join(current_chunk)
                if len(chunk_text.strip()) > 50:
                    chunks.append({
                        "artifact_id": original_artifact.id,
                        "source_url": original_artifact.url,
                        "section_path": current_section,
                        "chunk_index": len(chunks),
                        "text": chunk_text,  # Use "text" for consistency with README
                        "word_count": len(chunk_text.split())
                    })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking document {normalized_artifact.id}: {e}")
            return []

    def _generate_online_viewer_url(self, cik: str, accession_number: str, primary_document: str) -> str:
        """Generate SEC online document viewer URL."""
        accession_clean = accession_number.replace("-", "")
        return f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession_number}&xbrl_type=v"

    def _calculate_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _save_manifest(self, manifest: Dict, manifest_path: str):
        """Save manifest to disk."""
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def _update_summary_from_artifacts(self, artifacts: List[Artifact], summary: Dict):
        """Update summary statistics from artifacts."""
        for artifact in artifacts:
            if artifact.parse_status == "pending":
                summary["downloaded_count"] += 1
            elif artifact.parse_status == "success":
                summary["parsed_success"] += 1
            elif artifact.parse_status == "failed":
                summary["parsed_failed"] += 1
            else:
                # Assume cached/skipped
                summary["skipped_cached"] += 1
            
            if artifact.filed_at and (not summary["latest_filed_at"] or artifact.filed_at > summary["latest_filed_at"]):
                summary["latest_filed_at"] = artifact.filed_at

    def _calculate_quality_metrics(self, manifest: Dict, years: int) -> Dict:
        """Calculate quality metrics for the dossier."""
        artifacts = manifest.get("artifacts", [])
        
        # Count filings by form
        form_counts = {}
        latest_filed = None
        for artifact in artifacts:
            if artifact.get("type") == "filing" and artifact.get("form"):
                form = artifact["form"]
                form_counts[form] = form_counts.get(form, 0) + 1
                
                filed_at = artifact.get("filed_at")
                if filed_at and (not latest_filed or filed_at > latest_filed):
                    latest_filed = filed_at
        
        # Completeness checks
        completeness = {
            "has_recent_10k": form_counts.get("10-K", 0) >= min(years, 3),
            "has_recent_10q": form_counts.get("10-Q", 0) >= min(years * 4, 8),
            "has_recent_8k": form_counts.get("8-K", 0) > 0,  # At least one recent 8-K
            "has_xbrl": any(a.get("type") == "xbrl" for a in artifacts)
        }
        
        # Freshness
        freshness = {
            "latest_filed_at": latest_filed,
            "days_since_last_update": None
        }
        if latest_filed:
            latest_dt = datetime.strptime(latest_filed, "%Y-%m-%d")
            days_diff = (datetime.now() - latest_dt).days
            freshness["days_since_last_update"] = days_diff
        
        # Traceability
        traceability = {
            "manifest_artifacts_complete": len(artifacts) > 0,
            "all_artifacts_have_ids": all(a.get("id") for a in artifacts),
            "all_artifacts_have_urls": all(a.get("url") for a in artifacts if a.get("type") != "xbrl")
        }
        
        return {
            "completeness": completeness,
            "freshness": freshness,
            "traceability": traceability
        }

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build US company research dossiers (Optimized)")
    parser.add_argument("ticker", help="Stock ticker symbol")
    parser.add_argument("--years", type=int, default=3, help="Number of years of filings to fetch")
    parser.add_argument("--forms", nargs="+", default=["10-K", "10-Q", "8-K", "DEF 14A", "4"],
                        help="SEC form types to fetch")
    parser.add_argument("--no-ir", action="store_true", help="Skip IR materials")
    parser.add_argument("--max-filings", type=int, default=50, help="Max filings per form")
    parser.add_argument("--force-rebuild", action="store_true", help="Force rebuild even if cached")
    parser.add_argument("--normalize", choices=["none", "light", "deep"], default="light",
                        help="Normalization level")
    parser.add_argument("--fetch-mode", choices=["http", "browser_fallback"], default="http",
                        help="Fetch mode for IR materials")
    parser.add_argument("--workspace", help="Workspace root directory")
    parser.add_argument("--dossier-root", default=os.getenv("DOSSIER_ROOT"),
                       help="Dossier output directory")
    
    args = parser.parse_args()
    
    dossier_builder = USCCompanyDossier(workspace_root=args.workspace, dossier_root=args.dossier_root)
    result = dossier_builder.build_dossier(
        ticker=args.ticker,
        years=args.years,
        forms=args.forms,
        include_ir=not args.no_ir,
        max_filings_per_form=args.max_filings,
        force_rebuild=args.force_rebuild,
        normalize_level=args.normalize,
        fetch_mode=args.fetch_mode
    )
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()