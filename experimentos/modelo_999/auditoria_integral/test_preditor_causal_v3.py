import unittest
from preditor_causal_v3 import predict

T = '2022-10-30T18:00:00-03:00'
class CausalTests(unittest.TestCase):
    def setUp(self):
        self.current = dict(timestamp=T, available_at=T, votes_a=40, votes_b=60, counted_sections=50, total_sections=100)
        self.first = {'AA': dict(votes_a=60, votes_b=40, valid_votes=100, available_at='2022-10-03T00:00:00-03:00')}
        self.row = dict(scope='AA', timestamp=T, available_at=T, votes_a=70, votes_b=30)
    def test_future_generation_cannot_change_forecast(self):
        later = dict(self.row, timestamp='2022-10-30T18:01:00-03:00', available_at='2022-10-30T18:01:00-03:00')
        self.assertEqual(predict(self.current,self.first), predict(self.current,self.first,[later]))
    def test_unavailable_past_record_cannot_change_forecast(self):
        later = dict(self.row, available_at='2022-10-30T18:01:00-03:00')
        self.assertEqual(predict(self.current,self.first), predict(self.current,self.first,[later]))
    def test_stale_record_is_excluded(self):
        old = dict(self.row,timestamp='2022-10-30T17:54:59-03:00',available_at='2022-10-30T17:55:00-03:00')
        self.assertEqual(predict(self.current,self.first), predict(self.current,self.first,[old]))
    def test_unavailable_history_rejected(self):
        self.first['AA']['available_at']='2022-10-31T00:00:00-03:00'
        with self.assertRaises(ValueError): predict(self.current,self.first)
    def test_full_coverage_equals_observed(self):
        self.current['counted_sections']=100
        self.assertEqual(predict(self.current,self.first,[self.row])['forecast_a'], .4)
    def test_invalid_denominator_rejected(self):
        self.current['total_sections']=49
        with self.assertRaises(ValueError): predict(self.current,self.first)
    def test_shrinkage_formula_control(self):
        # raw swing=.1; applied=.025; unseen=.625; forecast=.5*.4+.5*.625
        self.assertAlmostEqual(predict(self.current,self.first,[self.row])['forecast_a'], .5125)
    def test_input_order_invariant(self):
        old = dict(self.row,timestamp='2022-10-30T17:59:00-03:00',available_at='2022-10-30T17:59:00-03:00',votes_a=20)
        self.assertEqual(predict(self.current,self.first,[old,self.row]),predict(self.current,self.first,[self.row,old]))
    def test_conflicting_snapshot_rejected(self):
        with self.assertRaises(ValueError): predict(self.current,self.first,[self.row,dict(self.row,votes_a=71)])
    def test_unavailable_national_rejected(self):
        self.current['available_at']='2022-10-30T18:01:00-03:00'
        with self.assertRaises(ValueError): predict(self.current,self.first)

class VersionComparison(unittest.TestCase):
    def test_explicit_quarter_swing(self):
        from preditor_causal_v2 import predict as v2
        c=dict(timestamp=T,available_at=T,votes_a=40,votes_b=60,counted_sections=50,total_sections=100)
        h={'AA':dict(votes_a=60,votes_b=40,valid_votes=100,available_at='2022-10-03T00:00:00-03:00')}
        rows=[dict(scope='AA',timestamp=T,available_at=T,votes_a=70,votes_b=30)]
        before=v2(c,h,rows);after=predict(c,h,rows)
        self.assertAlmostEqual(after['swing'], before['swing']*.25)
        self.assertEqual(after['raw_swing'],before['swing'])
    def test_no_swing_versions_coincide(self):
        from preditor_causal_v2 import predict as v2
        c=dict(timestamp=T,available_at=T,votes_a=40,votes_b=60,counted_sections=50,total_sections=100)
        h={'AA':dict(votes_a=60,votes_b=40,valid_votes=100,available_at='2022-10-03T00:00:00-03:00')}
        self.assertEqual(predict(c,h)['forecast_a'],v2(c,h)['forecast_a'])
if __name__ == '__main__': unittest.main()
