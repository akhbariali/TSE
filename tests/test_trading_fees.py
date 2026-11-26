"""Fee labels use both trade legs, not the sum of percentages or a 2% proxy."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from trading_fees import break_even,net_return


class FeeTests(unittest.TestCase):
    def test_break_even_and_positive_net_target(self):
        for market,buy in [('tse',.003712),('ifb',.003632)]:
            threshold=break_even(market)
            self.assertAlmostEqual(net_return(threshold,market),0)
            self.assertLess(net_return(threshold-.00001,market),0)
            self.assertGreater(net_return(threshold+.00001,market),0)
            self.assertGreater(threshold,buy+.0088)
            self.assertLess(threshold,.02)
            self.assertAlmostEqual(net_return(.02,market),1.02*.9912/(1+buy)-1)
        self.assertGreater(break_even('tse'),break_even('ifb'))


if __name__=='__main__':unittest.main()
