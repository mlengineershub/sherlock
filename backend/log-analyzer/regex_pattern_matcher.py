import re
from typing import Dict, List, Optional

class RegexPatternMatcher:
    def __init__(self):
        self.compiled_patterns = {}

    def match_pattern(self, log_entry: str, pattern: str) -> Optional[Dict]:
        """
        Match a log entry against a regex pattern with named groups
        Returns dict of named group matches or None if no match
        """
        if pattern not in self.compiled_patterns:
            try:
                self.compiled_patterns[pattern] = re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")

        match = self.compiled_patterns[pattern].match(log_entry)
        if match:
            return match.groupdict()
        return None

    def batch_match(self, log_entries: List[str], pattern: str) -> List[Optional[Dict]]:
        """
        Match multiple log entries against a pattern
        Returns list of match results (dict or None)
        """
        return [self.match_pattern(entry, pattern) for entry in log_entries]