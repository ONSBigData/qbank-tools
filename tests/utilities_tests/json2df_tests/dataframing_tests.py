import json

import nose.tools as nstools
import tests.helpers.patch_helper as patch_helper

from utilities.json2df import dataframing


class TestExtractUsefulAttrs:
    TC_NODE = {
        'path': ['segment', 'segment', 4, 'question', 2, 'tracking_code'],
        'value': 'c_e5',
        'attrs': [
            {'path': ['survey_scrape_info', 'file_name'], 'value': 'ex_sel002-ft0001.pdf'},
            {'path': ['survey_scrape_info', 'scrape_date'], 'value': '01/06/2017'},
            {'path': ['survey_scrape_info', 'folder_name'], 'value': '002 - Questionnaire Examples'},
            {'path': ['survey_scrape_info', 'download_date'], 'value': '24/03/2017'},
            {'path': ['segment', 'segment_type'], 'value': 'survey'},
            {'path': ['segment', 'survey_number'], 'value': '002'},
            {'path': ['segment', 'form_type'], 'value': '0001'},
            {'path': ['segment', 'reporting_period', 'end'], 'value': '31/12/2015'},
            {'path': ['segment', 'reporting_period', 'start'], 'value': '01/01/2015'},
            {'path': ['segment', 'text'], 'value': 'Survey of Research and Development Carried Out in the United Kingdom'},
            {'path': ['segment', 'segment', 4, 'text'], 'value': 'Section E - Workplace Information'},
            {'path': ['segment', 'segment', 4, 'question', 2, 'text'], 'value': 'Contact details'},
            {'path': ['segment', 'segment', 4, 'question', 2, 'type'], 'value': 'contact_6'},
            {'path': ['segment', 'segment', 4, 'question', 2, 'ID'], 'value': '29'},
            {'path': ['segment', 'segment', 4, 'question', 2, 'context'], 'value': 'context-value'},
            {'path': ['segment', 'segment', 4, 'question', 2, 'tracking_code'], 'value': 'c_e5'}
        ]
    }

    def test_extracts_correctly(self):
        actual = dataframing.extract_useful_attrs(self.TC_NODE)
        expected = {
            'sci_download_date': '24/03/2017',
            'sci_file_name': 'ex_sel002-ft0001.pdf',
            'sci_folder_name': '002 - Questionnaire Examples',
            'sci_scrape_date': '01/06/2017',
            's0_form_type': '0001',
            's0_reporting_period__end': '31/12/2015',
            's0_reporting_period__start': '01/01/2015',
            's0_segment_type': 'survey',
            's0_survey_number': '002',
            's0_text': 'Survey of Research and Development Carried Out in the United Kingdom',
            'i1_form_type': '0001',
            'i1_reporting_period__end': '31/12/2015',
            'i1_reporting_period__start': '01/01/2015',
            'i1_segment_type': 'survey',
            'i1_survey_number': '002',
            'i1_text': 'Survey of Research and Development Carried Out in the United Kingdom',
            's1_text': 'Section E - Workplace Information',
            'i0_text': 'Section E - Workplace Information',
            'q_context': 'context-value',
            'q_id': '29',
            'q_text': 'Contact details',
            'q_type': 'contact_6'
        }

        nstools.assert_dict_equal(actual, expected)

class TestCreateNewAttrs:
    def get_row(self):
        return {
            'tr_code': 'TR CODE',
            'path': 'PATH',
            'sci_download_date': '24/03/2017',
            'sci_file_name': 'ex_sel002-ft0001.pdf',
            'sci_folder_name': '002 - Questionnaire Examples',
            'sci_scrape_date': '01/06/2017',
            's0_form_type': '0001',
            's0_reporting_period__start': '01/01/2015',
            's0_reporting_period__end': '31/12/2015',
            's0_segment_type': 'survey',
            's0_survey_number': '002',
            's0_text': 'Survey of Research and Development Carried Out in the United Kingdom',
            'i1_form_type': '0001',
            'i1_reporting_period__end': '31/12/2015',
            'i1_reporting_period__start': '01/01/2015',
            'i1_segment_type': 'survey',
            'i1_survey_number': '002',
            'i1_text': 'Survey of Research and Development Carried Out in the United Kingdom',
            's1_text': 'Section E - Workplace Information',
            'i0_text': 'Section E - Workplace Information',
            'q_context': 'context-value',
            'q_id': '29',
            'q_text': 'Please provide here the contact details',
            'q_type': 'contact_6'
        }

    def test_creates_correctly(self):
        actual = dataframing.create_new_attrs(self.get_row())

        expected = {
            'all_context': 'context-value',
            'all_exclusions': '',
            'all_inclusions': '',
            'all_seg_text': 'Survey of Research and Development Carried Out in the United Kingdom ||| Section E - Workplace Information',
            'all_text': 'Survey of Research and Development Carried Out in the United Kingdom ||| Section E - Workplace Information ||| Please provide here the contact details',
            'close_seg_text': 'Survey of Research and Development Carried Out in the United Kingdom ||| Section E - Workplace Information',
            'first_text': 'Please provide here the contact details',
            'form_type': '0001',
            'period_days': 364,
            'period_end': '31/12/2015',
            'period_start': '01/01/2015',
            'qtext': 'Please provide here the contact details',
            'suff_qtext': 'Please provide here the contact details',
            'survey_id': '002',
            'type': 'contact_6',
            'uid': '002_0001_TR CODE'
        }

        nstools.assert_dict_equal(actual, expected)

    def test_gets_first_text_correctly(self):
        row = self.get_row()
        del row['q_text']

        actual = dataframing.create_new_attrs(row)

        expected_first_text = 'Section E - Workplace Information'

        nstools.assert_equals(actual['first_text'], expected_first_text)

    def test_gets_sufficient_text_correctly_when_qtext_not_long_enough(self):
        row = self.get_row()
        row['q_text'] = 'contact'

        actual = dataframing.create_new_attrs(row)

        expected_sufficient_qtext = 'Survey of Research and Development Carried Out in the United Kingdom ||| Section E - Workplace Information ||| contact'

        nstools.assert_equals(actual['suff_qtext'], expected_sufficient_qtext)

