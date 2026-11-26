"""Unit accounting, excluded assets, and concurrent private portfolio saves."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nav


class NavTests(unittest.TestCase):
    def book(self):
        b = nav.default_book()
        b.update(cash='2000000', confirmed=True, as_of='1405/09/04', holdings=[
            {'symbol': 'وساپا', 'value': '10000000'},
            {'symbol': 'توان1', 'value': '9000000'},
            {'symbol': 'آب', 'value': '3000000'},
            {'symbol': 'کاوان', 'value': '2000000'},
            {'symbol': 'خصدرا', 'value': '1000000'},
            {'symbol': 'خاور', 'value': '1000000'},
            {'symbol': 'وتوصا', 'value': '1000000'}])
        return b

    def test_equal_initial_capital_and_exclusions(self):
        r = nav.calculate(self.book())
        self.assertEqual(r['nav'], 12000000)
        self.assertEqual(r['excluded'], 17000000)
        self.assertEqual([p['profit'] for p in r['people']], [1000000, 1000000])
        self.assertEqual([p['ownership'] for p in r['people']], [.5, .5])

    def test_later_deposit_and_withdrawal_use_entry_nav(self):
        b = self.book()
        b['flows'] += [{'person': 'Me', 'date': '1405/09/01', 'amount': '2400000', 'unit_price': '1.2'},
                       {'person': 'Person 2', 'date': '1405/09/02', 'amount': '-1200000', 'unit_price': '1.2'}]
        b['cash'] = '3200000'
        r = nav.calculate(b)
        self.assertEqual(r['unit_price'], 1.2)
        self.assertEqual([p['profit'] for p in r['people']], [1000000, 1000000])
        self.assertEqual(sum(p['value'] for p in r['people']), r['nav'])

    def test_pending_is_not_zero_profit_and_losses_are_supported(self):
        self.assertIsNone(nav.calculate(nav.default_book())['people'][0]['profit'])
        b = self.book(); b['cash'] = '-2000000'
        self.assertEqual(nav.calculate(b)['people'][0]['profit'], -1000000)
        b['confirmed'] = False
        self.assertIsNone(nav.calculate(b)['nav'])

    def test_invalid_inputs_fail_before_saving(self):
        for key, value in [('cash', 'NaN'), ('cash', 'Infinity'), ('liabilities', '-1')]:
            b = self.book(); b[key] = value
            with self.assertRaises(ValueError): nav.calculate(b)
        b = self.book(); b['flows'][0]['amount'] = '-1'
        with self.assertRaises(ValueError): nav.calculate(b)
        b = self.book(); b['flows'][0]['unit_price'] = '0'
        with self.assertRaises(ValueError): nav.calculate(b)
        b = self.book(); b['cash'] = ''
        with self.assertRaises(ValueError): nav.calculate(b)

    def test_saved_revisions_survive_reload_and_stale_write_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(nav, 'DB', Path(folder)/'nav.db'):
            initial = nav.load()
            saved = nav.save({'revision': initial['revision'], 'book': self.book()})
            self.assertEqual(nav.load(), saved)
            with self.assertRaises(ValueError): nav.save({'revision': 0, 'book': self.book()})
            self.assertEqual(nav.load(), saved)

    def test_investor_response_contains_only_other_peoples_balances(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(nav, 'DB', Path(folder)/'nav.db'):
            book = self.book()
            book['note'] = 'Private owner notes'
            nav.save({'revision': 0, 'book': book})
            response = nav.balances()
            self.assertEqual(response['people'], [{'person': 'Person 2', 'net_contributed': 5000000,
                                                  'value': 6000000, 'profit': 1000000}])
            self.assertEqual(set(response), {'people', 'ready', 'as_of'})
            book['confirmed'] = False
            book['owner'] = 'Person 2'
            nav.save({'revision': 1, 'book': book})
            response = nav.balances()
            self.assertEqual(response['people'][0]['person'], 'Me')
            self.assertIsNone(response['people'][0]['value'])


if __name__ == '__main__': unittest.main()
