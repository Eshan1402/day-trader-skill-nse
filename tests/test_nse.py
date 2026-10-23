"""Offline checks for the NSE port: python3 -m unittest tests.test_nse -v"""
import datetime
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def load(skill, script):
    spec = importlib.util.spec_from_file_location(skill.replace("-", "_"), os.path.join(HERE, "..", skill, script))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scan = load("nse-scanner", "scan.py")
risk = load("nse-risk", "check.py")
tm = load("nse-timemachine", "timemachine.py")


class NSE(unittest.TestCase):
    def test_ist_both_ways(self):
        utc = datetime.datetime(2026, 10, 23, 3, 45)            # 09:15 IST
        self.assertEqual(scan.to_eastern(utc), datetime.datetime(2026, 10, 23, 9, 15))
        self.assertEqual(scan.parse_now("2026-10-23 09:15"), utc)
        self.assertEqual(risk.to_eastern(datetime.datetime(2026, 7, 1, 10, 0)).time(), datetime.time(15, 30))

    def test_session_and_holidays(self):
        self.assertEqual(scan.session(datetime.date(2026, 10, 23)), (datetime.time(9, 15), datetime.time(15, 30)))
        self.assertIsNone(scan.session(datetime.date(2026, 10, 20)))   # Dussehra
        self.assertIsNone(scan.session(datetime.date(2026, 10, 24)))   # Saturday
        self.assertEqual(tm.SESSION_BARS, 73)

    def test_universe_keeps_eq_only(self):
        text = ("SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING\n"
                "M&M,Mahindra & Mahindra Limited,EQ,03-JAN-1996\n"
                "BAJAJ-AUTO,Bajaj Auto Limited,EQ,26-MAY-2008\n"
                "SOMEBE,Some Limited,BE,01-JAN-2020\n")
        kept, counts, _ = scan.build_universe({"EQUITY_L.csv": text})
        self.assertEqual([s for s, _ in kept], ["BAJAJ-AUTO", "M&M"])
        self.assertEqual(counts["series BE"], 1)

    def test_yahoo_symbols(self):
        self.assertEqual(scan.to_yahoo("m&m"), "M%26M.NS")
        self.assertEqual(scan._from_yahoo("BAJAJ-AUTO.NS"), "BAJAJ-AUTO")
        for sym in ("M&M", "BAJAJ-AUTO", "3MINDIA", "RELIANCE"):
            self.assertTrue(risk.TICKER.match(sym), sym)
        self.assertFalse(risk.TICKER.match("RELIANCE.NS"))


if __name__ == "__main__":
    unittest.main()
