"""Optional trainer checks: future prices cannot alter past prediction features."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from model_recommendations import features,FEATURES
try:
    import pandas as pd
except ImportError:
    pd=None


@unittest.skipIf(pd is None,'Optional model environment is not installed')
class ModelFeatureTests(unittest.TestCase):
    def test_future_invariance_latest_rows_and_missing_session(self):
        base={'market':'tse','symbol':'x1','volume':100,'turnover_rial':2e9,
              'average_price_rial':100,'retail_flow_turnover_ratio':.1,
              'retail_buy_value_share':.6,'retail_sell_value_share':.5}
        rows=[{**base,'date':f'1405/08/{i:02}','closing_price_rial':100+i} for i in range(1,16)]
        dates=[r['date'] for r in rows]
        full=features(pd.DataFrame(rows),dates)
        short=features(pd.DataFrame(rows[:12]),dates[:12])
        pd.testing.assert_frame_equal(full.iloc[:12][FEATURES],short[FEATURES])
        self.assertTrue(pd.isna(short.iloc[-1].next_return))
        self.assertEqual(full.iloc[0].next_return,102/101-1)
        missing=features(pd.DataFrame([rows[0],rows[2]]),dates)
        self.assertTrue(pd.isna(missing.iloc[0].next_return))
        extreme=features(pd.DataFrame([rows[0],{**rows[1],'closing_price_rial':1000}]),dates)
        self.assertGreater(extreme.iloc[0].next_return, .25)


if __name__=='__main__':unittest.main()
