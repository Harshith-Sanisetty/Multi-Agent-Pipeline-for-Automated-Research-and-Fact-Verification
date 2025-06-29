import sqlite3
import re
from datetime import datetime
import threading

class ClaimTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect('research.db', check_same_thread=False)
        self._create_table()
    
    def _create_table(self):
        with self.lock:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY,
                claim TEXT,
                sources TEXT,
                status TEXT DEFAULT 'unverified',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            self.conn.commit()
    
    def extract_claims(self, text: str):
        """Improved claim extraction from agent output"""
        if not text:
            return []
        
        
        claims = re.findall(r'(?:\n\s*[-*•]|\d+\.)\s*(.+?)(?=\n|$)', text, re.MULTILINE)
        
        
        claim_indicators = ['compared to', 'better than', 'faster than', 'supports', 'offers', 'provides']
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(indicator in sentence.lower() for indicator in claim_indicators):
                claims.append(sentence)
        
        return [claim.strip() for claim in claims if len(claim) > 15]
    
    def add_claims(self, claims: list, sources: str):
        if not claims:
            return
        
        with self.lock:
            try:
                for claim in claims:
                    self.conn.execute(
                        "INSERT INTO claims (claim, sources) VALUES (?, ?)",
                        (claim, sources)
                    )
                self.conn.commit()
            except Exception as e:
                print(f"Error adding claims: {e}")
    
    def get_verification_report(self):
        with self.lock:
            try:
                cursor = self.conn.execute("""
                    SELECT status, COUNT(*) 
                    FROM claims 
                    GROUP BY status
                """)
                result = {row[0]: row[1] for row in cursor.fetchall()}
                
                
                if not result:
                    result = {'unverified': 0}
                
                return result
            except Exception as e:
                print(f"Error getting verification report: {e}")
                return {'unverified': 0}
    
    def close(self):
        with self.lock:
            if self.conn:
                self.conn.close()