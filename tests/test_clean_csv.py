import csv
import tempfile
import unittest
from pathlib import Path
from clean_csv import FIELDS, process, report_html, run, safe_cell

class CleanerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'input.csv'

    def write(self, rows, headers=FIELDS):
        with self.source.open('w',encoding='utf-8-sig',newline='') as h:
            writer = csv.writer(h);writer.writerow(headers);writer.writerows(rows)

    def test_normalization_unicode_and_email_local_part(self):
        self.write([[' 01 ',' Phương   Nguyễn ','Person@EXAMPLE.COM',' vn ']])
        accepted,_,_,stats = process(self.source)
        self.assertEqual(accepted,[dict(customer_id='01',name='Phương Nguyễn',email='Person@example.com',country='VN')])
        self.assertEqual(stats['normalized_records'],1)

    def test_duplicate_after_normalization(self):
        self.write([['1','A','a@example.com','US'],[' 1 ',' A ','a@EXAMPLE.COM','us']])
        a,r,_,s=process(self.source)
        self.assertEqual((len(a),len(r),s['duplicate_records']),(1,1,1))

    def test_invalid_first_record_does_not_remove_valid_record(self):
        self.write([['1','','a@example.com','US'],['1','A','a@example.com','US']])
        a,r,_,_=process(self.source)
        self.assertEqual((len(a),len(r)),(1,1))

    def test_validation_errors(self):
        self.write([['1','','bad email','USA'],['2','B','','US']])
        a,r,issues,_=process(self.source)
        self.assertFalse(a);self.assertEqual(len(r),2)
        self.assertTrue({'missing_name','invalid_email','invalid_country','missing_email'} <= {i['code'] for i in issues})

    def test_ragged_records(self):
        self.write([['1','A'],['2','B','b@example.com','US','extra']])
        a,r,_,_=process(self.source)
        self.assertFalse(a);self.assertEqual(len(r),2)

    def test_header_errors(self):
        self.write([],['customer_id','name','email','email'])
        with self.assertRaises(ValueError):process(self.source)
        self.write([],['customer_id','name'])
        with self.assertRaises(ValueError):process(self.source)

    def test_formula_and_html_escape(self):
        self.write([['1','=1+1','a@example.com','US'],['2','<script>alert(1)</script>','b@example.com','US']])
        a,r,i,s=process(self.source)
        self.assertEqual(len(r),1)
        rendered=report_html(s,a,r,i)
        self.assertNotIn('<script>',rendered)
        self.assertIn('&lt;script&gt;',rendered)
        self.assertEqual(safe_cell(' =1'),"' =1")

    def test_export_and_no_overwrite(self):
        self.write([['1','A','a@example.com','US']])
        out=self.root/'output'
        run(self.source,out)
        self.assertEqual(len(list(out.iterdir())),5)
        with self.assertRaises(ValueError):run(self.source,out)
        self.assertTrue(self.source.exists())

    def test_input_protection(self):
        self.source=self.root/'cleaned.csv'
        self.write([['1','A','a@example.com','US']])
        original=self.source.read_bytes()
        with self.assertRaises(ValueError):run(self.source,self.root)
        self.assertEqual(self.source.read_bytes(),original)

    def test_demo_accounting(self):
        path=Path(__file__).resolve().parents[1]/'demo'/'customers_messy.csv'
        a,r,_,s=process(path)
        self.assertEqual((s['input_records'],len(a),len(r)),(12,5,7))
        self.assertEqual(s['input_records'],s['accepted_records']+s['rejected_records'])

if __name__=='__main__':unittest.main()
