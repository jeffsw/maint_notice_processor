'''
This prototype parser is meant to "keep it simple" while allowing some
extensibility for handling diversely-formatted maintenance emails with
varying amounts of information.

If parsing HTML or other structured data, a different class might be
appropriate.

TODO: Collect some example emails with multiple impacted circuits and
re-factor to produce a MaintMessage containing one or more MaintForecastEvents.
'''
import argparse
import re
from .maint_notice_parser_base import MaintNoticeParserBase

class MaintNoticeParserText(MaintNoticeParserBase):
    '''
    Parse text maintenance notification emails.

    A dict of regexes is used for parsing.  The regex used is selected
    based on the email From: domain.
    '''
    re_collection = dict()

    ###
    # Dict of regexes which are compiled with flags to keep those the flags
    # and expressions together.
    re_collection['start_end_service_id_impact_n_x_n_units'] = re.compile('''
    (?P<beginToken>start|begin)
    [^0-9]+
    (?P<beginDatetime>[0-9]{4}-[a-z]{3,9}-[0-9]{2}\ [0-9]{2}:[0-9]{2}\ UTC)
    .*
    (?P<endToken>end)
    [^0-9]+
    (?P<endDatetime>[0-9]{4}-[a-z]{3,9}-[0-9]{2}\ [0-9]{2}:[0-9]{2}\ UTC)
    .*
    Service.ID:.(?P<parsedVendorCircuitId>[a-z0-9-]+)
    .*
    Impact:.(?P<impactMultiplier>[0-9]+)?.x.(?P<impactMultiplicand>[0-9]+).(?P<impactUnits>hours|minutes).interruption
    ''', flags=re.DOTALL|re.IGNORECASE|re.VERBOSE)

    # 'default' regex
    re_collection['default'] = re_collection['start_end_service_id_impact_n_x_n_units']
    # End dict of regexes
    ###

    # Maps provider email domains to names of regexes in re_collection dict
    re_provider_to_collection_map = {
        'fiberprovider.com': 'start_end_service_id_impact_n_x_n_units',
    }

    def parse_str(self, email_body:str, email_from:str=None) -> bool:
        '''
        Identify the maintenance beginWindow, endWindow, parsedVendorCircuitId,
        and impactDuration.

        Invokes methods handle_<token>(self, tokenName, tokenValue) to store
        relevant data in object attributes, for example, handle_beginWindow().

        Returns True if parsing successful.
        '''

        use_regex = self.re_collection['default']
        if email_from is not None:
            email_from_match = re.match('.*@(.+)', email_from)
            email_from_domain = email_from_match[1]
            if email_from_domain in self.re_provider_to_collection_map:
                use_re_name = self.re_provider_to_collection_map[email_from_domain]
                use_regex = self.re_collection[use_re_name]
            else:
                raise ValueError(F'email_from domain {email_from_domain} not found in re_provider_to_collection_map')

        re_gen = use_regex.finditer(email_body)
        for re_match in re_gen:
            match_dict = re_match.groupdict()
            for tokenName, tokenValue in match_dict.items():
                self.last_match_token = tokenName
                setter_method = getattr(self, 'handle_'+tokenName, None)
                if callable(setter_method):
                    setter_method(tokenName=tokenName, tokenValue=tokenValue)
        self.parse_finalize()
        return(self.is_parse_successful())

    @classmethod
    def cli_entry_point(cls):
        'Entry point for CLI testing.  Run with --help for usage.'
        ap = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
        ap.add_argument('--email-from', default=None, help='From: email address which sent the maintenance email')
        ap.add_argument('--input-file', required=True, help='Read maintenance email from given filename')
        args = vars(ap.parse_args())

        with open(args['input_file']) as email_file:
            email_body = email_file.read()

        mnparser = MaintNoticeParserText()
        mnparser.parse_str(email_body=email_body, email_from=args['email_from'])
        print(mnparser.serialize_notice_to_json())
