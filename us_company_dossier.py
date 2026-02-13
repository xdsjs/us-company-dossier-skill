#!/usr/bin/env python3
"""
US Company Dossier Skill (Simplified - Links Only)
Generates SEC filing metadata with online viewing links - no file downloads.
"""

import os
import json
import re
import time
import requests
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

# Load .env from project root
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Filing:
    """SEC filing metadata with links"""
    id: str
    form: str
    period: Optional[str] = None
    filed_at: str = ""
    accession_number: str = ""
    primary_document: str = ""
    url: str = ""
    viewer_url: str = ""
    description: Optional[str] = None

@dataclass
class CompanyInfo:
    ticker: str
    company_name: Optional[str] = None
    cik: Optional[str] = None
    exchange: Optional[str] = None

@dataclass
class RunInfo:
    run_id: str
    started_at: str
    ended_at: str
    status: str
    version: str = "2.0.0"

@dataclass
class ConfigSnapshot:
    years: int
    forms: List[str]
    max_filings_per_form: int
    sec_user_agent: str
    sec_rps_limit: int

class USCompanyDossier:
    def __init__(self, workspace_root: str = None, dossier_root: str = None):
        self.workspace_root = Path(workspace_root or os.getenv("WORKSPACE_ROOT", os.getcwd()))
        self.dossier_root = Path(dossier_root or os.getenv("DOSSIER_ROOT", self.workspace_root / "dossiers"))
        
        # SEC configuration
        self.sec_user_agent = os.getenv("SEC_USER_AGENT", "ResearchBot/1.0 (research@example.com)")
        self.sec_rps_limit = int(os.getenv("SEC_RPS_LIMIT", "3"))
        self.sec_base_url = "https://data.sec.gov"
        
        # Rate limiting
        self.min_request_interval = 1.0 / self.sec_rps_limit
        self.last_request_time = 0
        
        logger.info(f"Initialized dossier builder - workspace: {self.workspace_root}, dossiers: {self.dossier_root}")

    def _rate_limited_get(self, url: str) -> requests.Response:
        """Make rate-limited GET request to SEC"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        headers = {"User-Agent": self.sec_user_agent}
        response = requests.get(url, headers=headers)
        self.last_request_time = time.time()
        response.raise_for_status()
        return response

    def _resolve_ticker(self, ticker: str) -> tuple[str, str]:
        """Resolve ticker to CIK using SEC company tickers JSON"""
        logger.info(f"Resolving ticker {ticker} to CIK...")
        
        url = "https://www.sec.gov/files/company_tickers.json"
        response = self._rate_limited_get(url)
        tickers_data = response.json()
        
        ticker_upper = ticker.upper()
        for entry in tickers_data.values():
            if entry["ticker"].upper() == ticker_upper:
                cik = str(entry["cik_str"]).zfill(10)
                title = entry["title"]
                logger.info(f"Resolved {ticker} -> CIK {cik} ({title})")
                return cik, title
        
        raise ValueError(f"Ticker {ticker} not found in SEC database")

    def _fetch_submissions(self, cik: str) -> Dict:
        """Fetch company submissions metadata from SEC"""
        url = f"{self.sec_base_url}/submissions/CIK{cik}.json"
        logger.info(f"Fetching submissions for CIK {cik}...")
        response = self._rate_limited_get(url)
        return response.json()

    def _generate_sec_urls(self, cik: str, accession: str, primary_doc: str) -> tuple[str, str]:
        """Generate SEC document URL and viewer URL"""
        # Remove hyphens from accession number for URL path
        accession_no_hyphen = accession.replace("-", "")
        
        # Direct document URL
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_hyphen}/{primary_doc}"
        
        # SEC online viewer URL
        viewer_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={int(cik)}&accession_number={accession}&xbrl_type=v"
        
        return doc_url, viewer_url

    def _parse_filings(self, submissions: Dict, forms: List[str], years: int, max_per_form: int) -> List[Filing]:
        """Parse filings from submissions data"""
        filings = []
        cutoff_date = datetime.now() - timedelta(days=years * 365)
        
        recent = submissions.get("filings", {}).get("recent", {})
        forms_list = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        descriptions = recent.get("primaryDocDescription", [])
        report_dates = recent.get("reportDate", [])
        
        cik = submissions["cik"]
        
        # Count filings per form
        form_counts = {f: 0 for f in forms}
        
        for i in range(len(forms_list)):
            form = forms_list[i]
            if form not in forms:
                continue
            
            if form_counts[form] >= max_per_form:
                continue
            
            filing_date_str = filing_dates[i]
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
            
            if filing_date < cutoff_date:
                continue
            
            accession = accessions[i]
            primary_doc = primary_docs[i]
            doc_url, viewer_url = self._generate_sec_urls(str(cik), accession, primary_doc)
            
            period = report_dates[i] if i < len(report_dates) else None
            
            filing = Filing(
                id=f"{form.lower()}-{period or filing_date_str}",
                form=form,
                period=period,
                filed_at=filing_date.isoformat() + "Z",
                accession_number=accession,
                primary_document=primary_doc,
                url=doc_url,
                viewer_url=viewer_url,
                description=descriptions[i] if i < len(descriptions) else None
            )
            
            filings.append(filing)
            form_counts[form] += 1
        
        logger.info(f"Parsed {len(filings)} filings across {len([c for c in form_counts.values() if c > 0])} form types")
        return filings

    def _save_manifest(self, dossier_dir: Path, company: CompanyInfo, run_info: RunInfo, 
                      config: ConfigSnapshot, filings: List[Filing]):
        """Save manifest.json"""
        manifest = {
            "company": asdict(company),
            "run_info": asdict(run_info),
            "config_snapshot": asdict(config),
            "filings": [asdict(f) for f in filings]
        }
        
        manifest_path = dossier_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Saved manifest: {manifest_path}")

    def build_dossier(self, ticker: str, years: int = 3, 
                     forms: List[str] = None,
                     max_filings_per_form: int = 50,
                     force_rebuild: bool = False) -> Dict[str, Any]:
        """Build company dossier with SEC filing links"""
        
        if forms is None:
            forms = ["10-K", "10-Q", "8-K", "DEF 14A", "4"]
        
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"Building dossier for {ticker} (run_id: {run_id})")
        
        try:
            # Resolve ticker to CIK
            cik, company_name = self._resolve_ticker(ticker)
            
            # Fetch submissions
            submissions = self._fetch_submissions(cik)
            
            # Parse filings
            filings = self._parse_filings(submissions, forms, years, max_filings_per_form)
            
            # Prepare dossier directory
            ticker_upper = ticker.upper()
            dossier_dir = self.dossier_root / ticker_upper
            dossier_dir.mkdir(parents=True, exist_ok=True)
            
            logs_dir = dossier_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Company info
            company = CompanyInfo(
                ticker=ticker_upper,
                company_name=company_name,
                cik=cik,
                exchange=submissions.get("exchanges", [""])[0] if submissions.get("exchanges") else None
            )
            
            # Config snapshot
            config = ConfigSnapshot(
                years=years,
                forms=forms,
                max_filings_per_form=max_filings_per_form,
                sec_user_agent=self.sec_user_agent,
                sec_rps_limit=self.sec_rps_limit
            )
            
            # Run info
            ended_at = datetime.utcnow().isoformat() + "Z"
            run_info = RunInfo(
                run_id=run_id,
                started_at=started_at,
                ended_at=ended_at,
                status="success",
                version="2.0.0"
            )
            
            # Save manifest
            self._save_manifest(dossier_dir, company, run_info, config, filings)
            
            # Summary
            latest_filing = max(filings, key=lambda f: f.filed_at) if filings else None
            
            result = {
                "dossier_path": str(dossier_dir),
                "manifest_path": str(dossier_dir / "manifest.json"),
                "summary": {
                    "ticker": ticker_upper,
                    "cik": cik,
                    "company_name": company_name,
                    "total_filings": len(filings),
                    "latest_filed_at": latest_filing.filed_at if latest_filing else None,
                    "status": "success"
                }
            }
            
            logger.info(f"Dossier built successfully: {len(filings)} filings indexed")
            return result
            
        except Exception as e:
            logger.error(f"Failed to build dossier: {e}", exc_info=True)
            ended_at = datetime.utcnow().isoformat() + "Z"
            return {
                "dossier_path": None,
                "summary": {
                    "ticker": ticker,
                    "status": "failed",
                    "error": str(e)
                }
            }

    def update_dossier(self, ticker: str) -> Dict[str, Any]:
        """Update existing dossier with new filings"""
        ticker_upper = ticker.upper()
        dossier_dir = self.dossier_root / ticker_upper
        manifest_path = dossier_dir / "manifest.json"
        
        if not manifest_path.exists():
            logger.warning(f"No existing dossier found for {ticker}, building from scratch")
            return self.build_dossier(ticker)
        
        # Load existing manifest to get config
        with open(manifest_path) as f:
            existing_manifest = json.load(f)
        
        config = existing_manifest.get("config_snapshot", {})
        
        return self.build_dossier(
            ticker=ticker,
            years=config.get("years", 3),
            forms=config.get("forms"),
            max_filings_per_form=config.get("max_filings_per_form", 50)
        )

    def get_status(self, ticker: str) -> Dict[str, Any]:
        """Get dossier status"""
        ticker_upper = ticker.upper()
        dossier_dir = self.dossier_root / ticker_upper
        manifest_path = dossier_dir / "manifest.json"
        
        if not manifest_path.exists():
            return {"exists": False, "ticker": ticker_upper}
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        filings = manifest.get("filings", [])
        latest_filing = max(filings, key=lambda f: f["filed_at"]) if filings else None
        
        return {
            "exists": True,
            "ticker": ticker_upper,
            "company_name": manifest.get("company", {}).get("company_name"),
            "cik": manifest.get("company", {}).get("cik"),
            "total_filings": len(filings),
            "latest_filed_at": latest_filing["filed_at"] if latest_filing else None,
            "last_updated": manifest.get("run_info", {}).get("ended_at"),
            "manifest_path": str(manifest_path)
        }

    def list_filings(self, ticker: str, form: str = None, since: str = None) -> List[Dict]:
        """List filings with optional filters"""
        ticker_upper = ticker.upper()
        manifest_path = self.dossier_root / ticker_upper / "manifest.json"
        
        if not manifest_path.exists():
            return []
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        filings = manifest.get("filings", [])
        
        # Apply filters
        if form:
            filings = [f for f in filings if f["form"] == form]
        
        if since:
            since_date = datetime.fromisoformat(since.replace("Z", ""))
            filings = [f for f in filings if datetime.fromisoformat(f["filed_at"].replace("Z", "")) >= since_date]
        
        return filings


# Public API
def build_dossier(ticker: str, **kwargs) -> Dict[str, Any]:
    """Build company dossier - public API"""
    builder = USCompanyDossier(
        workspace_root=kwargs.pop("workspace_root", None),
        dossier_root=kwargs.pop("dossier_root", None)
    )
    return builder.build_dossier(ticker, **kwargs)

def update_dossier(ticker: str, **kwargs) -> Dict[str, Any]:
    """Update existing dossier - public API"""
    builder = USCompanyDossier(
        workspace_root=kwargs.pop("workspace_root", None),
        dossier_root=kwargs.pop("dossier_root", None)
    )
    return builder.update_dossier(ticker)

def status(ticker: str, **kwargs) -> Dict[str, Any]:
    """Get dossier status - public API"""
    builder = USCompanyDossier(
        workspace_root=kwargs.pop("workspace_root", None),
        dossier_root=kwargs.pop("dossier_root", None)
    )
    return builder.get_status(ticker)

def list_filings(ticker: str, **kwargs) -> List[Dict]:
    """List filings - public API"""
    builder = USCompanyDossier(
        workspace_root=kwargs.pop("workspace_root", None),
        dossier_root=kwargs.pop("dossier_root", None)
    )
    return builder.list_filings(ticker, **kwargs)
