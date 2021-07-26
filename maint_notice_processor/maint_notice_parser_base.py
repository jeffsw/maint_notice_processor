import dateutil.parser
import json

class MaintNoticeParserBase():
    '''
    Parser classes can inherit from this super-class.  It provides most
    of the methods they'll need, except the actual text parsing, which
    is an exercise for those sub-classes.
    '''

    required_attrs_present = ['beginWindow', 'endWindow', 'parsedVendorCircuitId']
    required_attrs_not_none = ['beginWindow', 'endWindow', 'parsedVendorCircuitId']

    def __init__(
        self,
    ):
        self.last_match_token = None

    def handle_beginDatetime(self, tokenName:str, tokenValue:str):
        parsed_date = dateutil.parser.parse(tokenValue)
        self.beginWindow = parsed_date

    def handle_endDatetime(self, tokenName:str, tokenValue:str):
        parsed_date = dateutil.parser.parse(tokenValue)
        self.endWindow = parsed_date

    def handle_impactMultiplicand(self, tokenName:str, tokenValue:str):
        converted = int(tokenValue)
        self.impactMultiplicand = converted

    def handle_impactMultiplier(self, tokenName:str, tokenValue:str):
        converted = int(tokenValue)
        self.impactMultiplier = converted
    
    def handle_impactUnits(self, tokenName:str, tokenValue:str):
        lowered = tokenValue.lower()
        if lowered in ['minute', 'minutes']:
            self.impactUnits = 'minutes'
        elif lowered in ['hour', 'hours']:
            self.impactUnits = 'hours'
        else:
            raise ValueError(F'impactUnits should be minute(s) or hour(s); got unexpected value: {tokenValue}')

    def handle_parsedVendorCircuitId(self, tokenName:str, tokenValue:str):
        self.parsedVendorCircuitId = tokenValue

    def is_parse_successful(self) -> bool:
        '''
        Check if all required_attrs_present and required_attrs_not_none
        conditions are satisfied.  Return True on success or False on failure.
        '''
        for attrName in self.required_attrs_present:
            if not hasattr(self, attrName):
                # Could raise AttributeError instead
                return False
        for attrName in self.required_attrs_not_none:
            if getattr(self, attrName, None) == None:
                # Could raise ValueError instead
                return False
        return True

    def parse_finalize(self):
        '''
        Check if there is arithmetic to be done on optional fields.
        '''
        if hasattr(self, 'impactMultiplicand') or hasattr(self, 'impactMultiplier') or hasattr(self, 'impactUnits'):
            # If any one of these three attributes is present, all three should be.
            # If one is missing and AttributeError is raised, that is Working As Intended.
            if self.impactUnits == 'minutes':
                unitMultiplier = 60
            elif self.impactUnits == 'hours':
                unitMultiplier = 3600
            else:
                raise ValueError(F'impactUnits should be seconds or minutes but it is an unrecognized value: F{self.impactUnits}')
            self.impactSeconds = self.impactMultiplicand * self.impactMultiplier * unitMultiplier

    def serialize_notice_to_json(self) -> str:
        '''
        Return a JSON-serialized string representing the maintenance
        notice data.  Does not include all parser state!

        Really, would create a class maintForecastEvent; with methods
        for database store/load and similar.  But, for quick prototype,
        this will do.
        '''
        d = dict()

        d['objectType'] = 'maintForecastEvent'
        d['beginWindow'] = str(self.beginWindow)
        d['endWindow'] = str(self.endWindow)

        # If impactSeconds directly known, use that value.
        # Otherwise, assume entire window is impact time.
        if hasattr(self, 'impactSeconds'):
            d['impactSeconds'] = self.impactSeconds
        else:
            impactDelta = self.endWindow - self.beginWindow
            d['impactSeconds'] = impactDelta.seconds

        if hasattr(self, 'parsedVendorCircuitId'):
            d['parsedVendorCircuitId'] = self.parsedVendorCircuitId

        j = json.dumps(d, indent=4, sort_keys=True)
        return j
