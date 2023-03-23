from __future__ import print_function
import datetime, traceback
from calendar import timegm, monthrange
from six import integer_types, string_types

import pytz

import ib_rrule as rrule

# https://datatracker.ietf.org/doc/html/rfc5545

MAX_SPANS = 100

SUPPORTED_TIMEZONES = set([
    "UTC",
    "Europe/Berlin",
    "Europe/London",
    "Europe/Paris",
    "US/Central",
    "US/Eastern",
    "US/Michigan",
    "US/Mountain",
    "US/Pacific",
    "Africa/Abidjan",
    "Africa/Accra",
    "Africa/Addis_Ababa",
    "Africa/Algiers",
    "Africa/Asmara",
    "Africa/Asmera",
    "Africa/Bamako",
    "Africa/Bangui",
    "Africa/Banjul",
    "Africa/Bissau",
    "Africa/Blantyre",
    "Africa/Brazzaville",
    "Africa/Bujumbura",
    "Africa/Cairo",
    "Africa/Casablanca",
    "Africa/Ceuta",
    "Africa/Conakry",
    "Africa/Dakar",
    "Africa/Dar_es_Salaam",
    "Africa/Djibouti",
    "Africa/Douala",
    "Africa/El_Aaiun",
    "Africa/Freetown",
    "Africa/Gaborone",
    "Africa/Harare",
    "Africa/Johannesburg",
    "Africa/Juba",
    "Africa/Kampala",
    "Africa/Khartoum",
    "Africa/Kigali",
    "Africa/Kinshasa",
    "Africa/Lagos",
    "Africa/Libreville",
    "Africa/Lome",
    "Africa/Luanda",
    "Africa/Lubumbashi",
    "Africa/Lusaka",
    "Africa/Malabo",
    "Africa/Maputo",
    "Africa/Maseru",
    "Africa/Mbabane",
    "Africa/Mogadishu",
    "Africa/Monrovia",
    "Africa/Nairobi",
    "Africa/Ndjamena",
    "Africa/Niamey",
    "Africa/Nouakchott",
    "Africa/Ouagadougou",
    "Africa/Porto-Novo",
    "Africa/Sao_Tome",
    "Africa/Timbuktu",
    "Africa/Tripoli",
    "Africa/Tunis",
    "Africa/Windhoek",
    "America/Adak",
    "America/Anchorage",
    "America/Anguilla",
    "America/Antigua",
    "America/Araguaina",
    "America/Argentina/Buenos_Aires",
    "America/Argentina/Catamarca",
    "America/Argentina/ComodRivadavia",
    "America/Argentina/Cordoba",
    "America/Argentina/Jujuy",
    "America/Argentina/La_Rioja",
    "America/Argentina/Mendoza",
    "America/Argentina/Rio_Gallegos",
    "America/Argentina/Salta",
    "America/Argentina/San_Juan",
    "America/Argentina/San_Luis",
    "America/Argentina/Tucuman",
    "America/Argentina/Ushuaia",
    "America/Aruba",
    "America/Asuncion",
    "America/Atikokan",
    "America/Atka",
    "America/Bahia",
    "America/Bahia_Banderas",
    "America/Barbados",
    "America/Belem",
    "America/Belize",
    "America/Blanc-Sablon",
    "America/Boa_Vista",
    "America/Bogota",
    "America/Boise",
    "America/Buenos_Aires",
    "America/Cambridge_Bay",
    "America/Campo_Grande",
    "America/Cancun",
    "America/Caracas",
    "America/Catamarca",
    "America/Cayenne",
    "America/Cayman",
    "America/Chicago",
    "America/Chihuahua",
    "America/Coral_Harbour",
    "America/Cordoba",
    "America/Costa_Rica",
    "America/Creston",
    "America/Cuiaba",
    "America/Curacao",
    "America/Danmarkshavn",
    "America/Dawson",
    "America/Dawson_Creek",
    "America/Denver",
    "America/Detroit",
    "America/Dominica",
    "America/Edmonton",
    "America/Eirunepe",
    "America/El_Salvador",
    "America/Ensenada",
    "America/Fort_Wayne",
    "America/Fortaleza",
    "America/Glace_Bay",
    "America/Godthab",
    "America/Goose_Bay",
    "America/Grand_Turk",
    "America/Grenada",
    "America/Guadeloupe",
    "America/Guatemala",
    "America/Guayaquil",
    "America/Guyana",
    "America/Halifax",
    "America/Havana",
    "America/Hermosillo",
    "America/Indiana/Indianapolis",
    "America/Indiana/Knox",
    "America/Indiana/Marengo",
    "America/Indiana/Petersburg",
    "America/Indiana/Tell_City",
    "America/Indiana/Vevay",
    "America/Indiana/Vincennes",
    "America/Indiana/Winamac",
    "America/Indianapolis",
    "America/Inuvik",
    "America/Iqaluit",
    "America/Jamaica",
    "America/Jujuy",
    "America/Juneau",
    "America/Kentucky/Louisville",
    "America/Kentucky/Monticello",
    "America/Knox_IN",
    "America/Kralendijk",
    "America/La_Paz",
    "America/Lima",
    "America/Los_Angeles",
    "America/Louisville",
    "America/Lower_Princes",
    "America/Maceio",
    "America/Managua",
    "America/Manaus",
    "America/Marigot",
    "America/Martinique",
    "America/Matamoros",
    "America/Mazatlan",
    "America/Mendoza",
    "America/Menominee",
    "America/Merida",
    "America/Metlakatla",
    "America/Mexico_City",
    "America/Miquelon",
    "America/Moncton",
    "America/Monterrey",
    "America/Montevideo",
    "America/Montreal",
    "America/Montserrat",
    "America/Nassau",
    "America/New_York",
    "America/Nipigon",
    "America/Nome",
    "America/Noronha",
    "America/North_Dakota/Beulah",
    "America/North_Dakota/Center",
    "America/North_Dakota/New_Salem",
    "America/Ojinaga",
    "America/Panama",
    "America/Pangnirtung",
    "America/Paramaribo",
    "America/Phoenix",
    "America/Port-au-Prince",
    "America/Port_of_Spain",
    "America/Porto_Acre",
    "America/Porto_Velho",
    "America/Puerto_Rico",
    "America/Rainy_River",
    "America/Rankin_Inlet",
    "America/Recife",
    "America/Regina",
    "America/Resolute",
    "America/Rio_Branco",
    "America/Rosario",
    "America/Santa_Isabel",
    "America/Santarem",
    "America/Santiago",
    "America/Santo_Domingo",
    "America/Sao_Paulo",
    "America/Scoresbysund",
    "America/Shiprock",
    "America/Sitka",
    "America/St_Barthelemy",
    "America/St_Johns",
    "America/St_Kitts",
    "America/St_Lucia",
    "America/St_Thomas",
    "America/St_Vincent",
    "America/Swift_Current",
    "America/Tegucigalpa",
    "America/Thule",
    "America/Thunder_Bay",
    "America/Tijuana",
    "America/Toronto",
    "America/Tortola",
    "America/Vancouver",
    "America/Virgin",
    "America/Whitehorse",
    "America/Winnipeg",
    "America/Yakutat",
    "America/Yellowknife",
    "Asia/Aden",
    "Asia/Almaty",
    "Asia/Amman",
    "Asia/Anadyr",
    "Asia/Aqtau",
    "Asia/Aqtobe",
    "Asia/Ashgabat",
    "Asia/Ashkhabad",
    "Asia/Baghdad",
    "Asia/Bahrain",
    "Asia/Baku",
    "Asia/Bangkok",
    "Asia/Beirut",
    "Asia/Bishkek",
    "Asia/Brunei",
    "Asia/Calcutta",
    "Asia/Choibalsan",
    "Asia/Chongqing",
    "Asia/Chungking",
    "Asia/Colombo",
    "Asia/Dacca",
    "Asia/Damascus",
    "Asia/Dhaka",
    "Asia/Dili",
    "Asia/Dubai",
    "Asia/Dushanbe",
    "Asia/Gaza",
    "Asia/Harbin",
    "Asia/Hebron",
    "Asia/Ho_Chi_Minh",
    "Asia/Hong_Kong",
    "Asia/Hovd",
    "Asia/Irkutsk",
    "Asia/Istanbul",
    "Asia/Jakarta",
    "Asia/Jayapura",
    "Asia/Jerusalem",
    "Asia/Kabul",
    "Asia/Kamchatka",
    "Asia/Karachi",
    "Asia/Kashgar",
    "Asia/Kathmandu",
    "Asia/Katmandu",
    "Asia/Kolkata",
    "Asia/Krasnoyarsk",
    "Asia/Kuala_Lumpur",
    "Asia/Kuching",
    "Asia/Kuwait",
    "Asia/Macao",
    "Asia/Macau",
    "Asia/Magadan",
    "Asia/Makassar",
    "Asia/Manila",
    "Asia/Muscat",
    "Asia/Nicosia",
    "Asia/Novokuznetsk",
    "Asia/Novosibirsk",
    "Asia/Omsk",
    "Asia/Oral",
    "Asia/Phnom_Penh",
    "Asia/Pontianak",
    "Asia/Pyongyang",
    "Asia/Qatar",
    "Asia/Qyzylorda",
    "Asia/Rangoon",
    "Asia/Riyadh",
    "Asia/Saigon",
    "Asia/Sakhalin",
    "Asia/Samarkand",
    "Asia/Seoul",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Asia/Taipei",
    "Asia/Tashkent",
    "Asia/Tbilisi",
    "Asia/Tehran",
    "Asia/Tel_Aviv",
    "Asia/Thimbu",
    "Asia/Thimphu",
    "Asia/Tokyo",
    "Asia/Ujung_Pandang",
    "Asia/Ulaanbaatar",
    "Asia/Ulan_Bator",
    "Asia/Urumqi",
    "Asia/Vientiane",
    "Asia/Vladivostok",
    "Asia/Yakutsk",
    "Asia/Yekaterinburg",
    "Asia/Yerevan",
    "Atlantic/Azores",
    "Atlantic/Bermuda",
    "Atlantic/Canary",
    "Atlantic/Cape_Verde",
    "Atlantic/Faeroe",
    "Atlantic/Faroe",
    "Atlantic/Jan_Mayen",
    "Atlantic/Madeira",
    "Atlantic/Reykjavik",
    "Atlantic/South_Georgia",
    "Atlantic/St_Helena",
    "Atlantic/Stanley",
    "Australia/ACT",
    "Australia/Adelaide",
    "Australia/Brisbane",
    "Australia/Broken_Hill",
    "Australia/Canberra",
    "Australia/Currie",
    "Australia/Darwin",
    "Australia/Eucla",
    "Australia/Hobart",
    "Australia/LHI",
    "Australia/Lindeman",
    "Australia/Lord_Howe",
    "Australia/Melbourne",
    "Australia/NSW",
    "Australia/North",
    "Australia/Perth",
    "Australia/Queensland",
    "Australia/South",
    "Australia/Sydney",
    "Australia/Tasmania",
    "Australia/Victoria",
    "Australia/West",
    "Australia/Yancowinna",
    "Brazil/Acre",
    "Brazil/DeNoronha",
    "Brazil/East",
    "Brazil/West",
    "Canada/Atlantic",
    "Canada/Central",
    "Canada/Eastern",
    "Canada/Mountain",
    "Canada/Newfoundland",
    "Canada/Pacific",
    "Canada/Saskatchewan",
    "Canada/Yukon",
    "Chile/Continental",
    "Chile/EasterIsland",
    "Cuba",
    "Egypt",
    "Eire",
    "Europe/Amsterdam",
    "Europe/Andorra",
    "Europe/Athens",
    "Europe/Belfast",
    "Europe/Belgrade",
    "Europe/Bratislava",
    "Europe/Brussels",
    "Europe/Bucharest",
    "Europe/Budapest",
    "Europe/Chisinau",
    "Europe/Copenhagen",
    "Europe/Dublin",
    "Europe/Gibraltar",
    "Europe/Guernsey",
    "Europe/Helsinki",
    "Europe/Isle_of_Man",
    "Europe/Istanbul",
    "Europe/Jersey",
    "Europe/Kaliningrad",
    "Europe/Kiev",
    "Europe/Lisbon",
    "Europe/Ljubljana",
    "Europe/Luxembourg",
    "Europe/Madrid",
    "Europe/Malta",
    "Europe/Mariehamn",
    "Europe/Minsk",
    "Europe/Monaco",
    "Europe/Moscow",
    "Europe/Nicosia",
    "Europe/Oslo",
    "Europe/Podgorica",
    "Europe/Prague",
    "Europe/Riga",
    "Europe/Rome",
    "Europe/Samara",
    "Europe/San_Marino",
    "Europe/Sarajevo",
    "Europe/Simferopol",
    "Europe/Skopje",
    "Europe/Sofia",
    "Europe/Stockholm",
    "Europe/Tallinn",
    "Europe/Tirane",
    "Europe/Tiraspol",
    "Europe/Uzhgorod",
    "Europe/Vaduz",
    "Europe/Vatican",
    "Europe/Vienna",
    "Europe/Vilnius",
    "Europe/Volgograd",
    "Europe/Warsaw",
    "Europe/Zagreb",
    "Europe/Zaporozhye",
    "Europe/Zurich",
    "Hongkong",
    "Iceland",
    "Indian/Antananarivo",
    "Indian/Chagos",
    "Indian/Christmas",
    "Indian/Cocos",
    "Indian/Comoro",
    "Indian/Kerguelen",
    "Indian/Mahe",
    "Indian/Maldives",
    "Indian/Mauritius",
    "Indian/Mayotte",
    "Indian/Reunion",
    "Israel",
    "Jamaica",
    "Japan",
    "Mexico/BajaNorte",
    "Mexico/BajaSur",
    "Mexico/General",
    "Pacific/Apia",
    "Pacific/Auckland",
    "Pacific/Chatham",
    "Pacific/Chuuk",
    "Pacific/Easter",
    "Pacific/Efate",
    "Pacific/Enderbury",
    "Pacific/Fakaofo",
    "Pacific/Fiji",
    "Pacific/Funafuti",
    "Pacific/Galapagos",
    "Pacific/Gambier",
    "Pacific/Guadalcanal",
    "Pacific/Guam",
    "Pacific/Honolulu",
    "Pacific/Johnston",
    "Pacific/Kiritimati",
    "Pacific/Kosrae",
    "Pacific/Kwajalein",
    "Pacific/Majuro",
    "Pacific/Marquesas",
    "Pacific/Midway",
    "Pacific/Nauru",
    "Pacific/Niue",
    "Pacific/Norfolk",
    "Pacific/Noumea",
    "Pacific/Pago_Pago",
    "Pacific/Palau",
    "Pacific/Pitcairn",
    "Pacific/Pohnpei",
    "Pacific/Ponape",
    "Pacific/Port_Moresby",
    "Pacific/Rarotonga",
    "Pacific/Saipan",
    "Pacific/Samoa",
    "Pacific/Tahiti",
    "Pacific/Tarawa",
    "Pacific/Tongatapu",
    "Pacific/Truk",
    "Pacific/Wake",
    "Pacific/Wallis",
    "Pacific/Yap",
    "Poland",
    "Portugal",
    "Singapore",
    "Turkey",
    "US/Alaska",
    "US/Aleutian",
    "US/Arizona",
    "US/East-Indiana",
    "US/Hawaii",
    "US/Indiana-Starke",
    "US/Samoa",
])

def dt_to_unix(dt):
    return timegm(dt.timetuple())
def utc_to_local(utc_dt, tz):
    return pytz.utc.localize(utc_dt).astimezone(tz).replace(tzinfo=None)
def local_to_utc(local_dt):
    return local_dt.astimezone(pytz.utc).replace(tzinfo=None)

def _omit_none(d):
    return dict(
        (k, v) for k, v in d.items()
        if v is not None
    )

DAY_MINUTES = 24 * 60

def schedule_localize(tz, dt_local):
    try:
        return tz.localize(dt_local, is_dst=None)
    except pytz.exceptions.AmbiguousTimeError:
        # print("abiguous uh oh")
        return min(
            tz.localize(dt_local, is_dst=True),
            tz.localize(dt_local, is_dst=False),
        )
    except pytz.exceptions.NonExistentTimeError:
        # print("non-existing uh oh. using later")
        return max(
            tz.localize(dt_local, is_dst=True),
            tz.localize(dt_local, is_dst=False),
        )

class TimeSpecError(Exception):
    pass

def verified_timezone(timezone):
    if not isinstance(timezone, string_types):
        raise TimeSpecError("Invalid timezone")
    if not timezone in SUPPORTED_TIMEZONES:
        raise TimeSpecError("Unsupported timezone. Contact support.")
    try:
        tz = pytz.timezone(timezone)
    except Exception as err:
        raise TimeSpecError("Unknown timezone")
    return tz

def timespec_from_config(value):
    if value == 'always':
        return AlwaysSpec()
    elif value == 'never':
        return NeverSpec()
    else:
        return TimeSpec.from_trusted_spec(value)

class AlwaysSpec(object):
    def spans_between(self, tz, dt_naive_local_min, dt_naive_local_max):
        return [(dt_naive_local_min, dt_naive_local_max)]
    def serialize(self):
        return 'always'

class NeverSpec(object):
    def spans_between(self, tz, dt_naive_local_min, dt_naive_local_max):
        return []
    def serialize(self):
        return 'never'

class TimeSpec(object):
    @classmethod
    def from_spec(cls, spec):
        if not isinstance(spec, dict):
            raise TimeSpecError("Top-level dict expected")

        if not 'start' in spec:
            raise TimeSpecError("Start missing")
        start = spec['start']
        if not isinstance(start, string_types):
            raise TimeSpecError("Invalid start: Not a string value")
        try:
            start = datetime.datetime.strptime(start, "%Y-%m-%d")
        except Exception as err:
            raise TimeSpecError("Invalid start: YYYY-MM-DD expected")
        dt_start = start

        repeat = spec.get('repeat', dict(freq='daily', count=1))
        if not isinstance(repeat, dict):
            raise TimeSpecError("Repeat must be dict")

        if not 'freq' in repeat:
            raise TimeSpecError("Freq missing")
        freq = repeat['freq']

        if freq == 'weekly' and start.weekday() != 0:
            raise TimeSpecError("Weekly schedule must start on a Monday")
        elif freq == 'monthly' and start.day != 1:
            raise TimeSpecError("Monthly schedule must start on the first of the month")

        rr_freq_map = dict(
            daily = (rrule.DAILY, DAY_MINUTES),
            weekly = (rrule.WEEKLY, 7 * DAY_MINUTES),
            monthly = (rrule.MONTHLY, 31 * DAY_MINUTES),
        )
        if not freq in rr_freq_map:
            raise TimeSpecError("Invalid freq. Use 'daily', 'weekly' or 'monthly'")
        freq, max_span_offset_value = rr_freq_map[freq]

        if not 'spans' in spec:
            raise TimeSpecError("Spans missing")
        spans = spec['spans']
        if not isinstance(spans, list):
            raise TimeSpecError("Spans must be list")
        if not spans:
            raise TimeSpecError("Schedule needs at least one span")
        if len(spans) > MAX_SPANS:
            raise TimeSpecError("Too many spans in time spec. Max allowed is %d" % (
                MAX_SPANS,
            ))
        for span in spans:
            if not isinstance(span, list):
                raise TimeSpecError("Span element must be list")
            if len(span) != 2:
                raise TimeSpecError("Span element must be two element list")
        pos = -1
        for min_offset, max_offset in spans:
            if not isinstance(min_offset, integer_types):
                raise TimeSpecError("Span boundary must be integer")
            if not isinstance(max_offset, integer_types):
                raise TimeSpecError("Span boundary must be integer")
            if min_offset < 0 or max_offset > max_span_offset_value:
                raise TimeSpecError("Invalid span: Outside of allowed range")
            if min_offset <= pos:
                raise TimeSpecError("Invalid span: Wrong order or overlapping")
            if max_offset <= min_offset:
                raise TimeSpecError("Invalid span: Invalid or empty boundaries")
            pos = max_offset

        if 'until' in repeat and 'count' in repeat:
            raise TimeSpecError("Cannot specify both until and count")

        if 'until' in repeat:
            until = repeat['until']
            if not isinstance(until, string_types):
                raise TimeSpecError("Invalid until")
            try:
                 until = datetime.datetime.strptime(until, "%Y-%m-%d")
            except Exception as err:
                raise TimeSpecError("Invalid 'until' format: YYYY-MM-DD expected")
            if until < dt_start:
                raise TimeSpecError("Invalid 'until': before start")
        else:
            until = None

        if 'count' in repeat:
            count = repeat['count']
            if not isinstance(count, integer_types):
                raise TimeSpecError("Invalid count")
            if count < 1:
                raise TimeSpecError("Count must be greater or equal to 1")
        else:
            count = None

        if 'interval' in repeat:
            interval = repeat['interval']
            if not isinstance(interval, integer_types):
                raise TimeSpecError("Invalid interval")
            if interval < 1:
                raise TimeSpecError("Interval must be greater or equal to 1")
        else:
            interval = 1

        def parse_list(key, validate):
            if not key in repeat:
                return None
            value = repeat[key]
            if not isinstance(value, list):
                raise TimeSpecError("List of expected for %s" % (key,))
            if not value:
                raise TimeSpecError("List for %s cannot be empty" % (key,))
            validated = set()
            for n, v in enumerate(value):
                v = validate(v)
                if v in validated:
                    raise TimeSpecError("Duplicate value %d in %s" % (v, key))
                validated.add(v)
            def keyfn(v):
                return repr(v)
            return sorted(validated, key=keyfn)

        def validate_by_weekday(v):
            if isinstance(v, integer_types):
                if v < 0 or v > 6:
                    raise TimeSpecError("by_weekday value outside valid range (0-6)")
                return rrule.weekday(v)
            if isinstance(v, list):
                if freq not in (rrule.MONTHLY, rrule.YEARLY):
                    raise TimeSpecError("by_weekday offset rule can only be used for monthly/yearly event")
                if len(v) != 2:
                    raise TimeSpecError("by_weekday list item must be list of two elements")
                wday, n = v
                if not isinstance(wday, integer_types):
                    raise TimeSpecError("by_weekday list item weekday mut be number")
                if wday < 0 or wday > 6:
                    raise TimeSpecError("by_weekday list item weekday outside valid range (0-6)")
                if not isinstance(n, integer_types):
                    raise TimeSpecError("by_weekday list item day offset must be number")
                if n == 0:
                    raise TimeSpecError("by_weekday list item day offset cannot be 0")
                if freq == rrule.MONTHLY and (n > 5 or n < -5):
                    raise TimeSpecError("by_weekday list item day offset must be between -5 and 5")
                elif freq == rrule.YEARLY and n > 364 or n < -364:
                    raise TimeSpecError("by_weekday list item day offset must be between -364 and 364")
                return rrule.weekday(wday, n)
            else:
                raise TimeSpecError("by_weekday value must be a number or tuple list")
        by_weekday = parse_list('by_weekday', validate_by_weekday)

        def validate_by_month(v):
            if not isinstance(v, integer_types):
                raise TimeSpecError("by_month value must be a number")
            if v < 1 or v > 12:
                raise TimeSpecError("by_month value outside valid range (1-12)")
            return v
        by_month = parse_list('by_month', validate_by_month)

        def validate_by_monthday(v):
            if not isinstance(v, integer_types):
                raise TimeSpecError("by_monthday value must be a number")
            if not (1 <= v <= 31 or -31 <= v <= 1):
                raise TimeSpecError("by_monthday value outside valid range (-31-1 or 1-31)")
            return v
        by_monthday = parse_list('by_monthday', validate_by_monthday)

        def validate_by_yearday(v):
            if not isinstance(v, integer_types):
                raise TimeSpecError("by_yearday value must be a number")
            if not (1 <= v <= 366 or -366 <= v <= 1):
                raise TimeSpecError("by_yearday value outside valid range (-366-1 or 1-366)")
            return v
        by_yearday = parse_list('by_yearday', validate_by_yearday)

        def validate_by_weekno(v):
            if not isinstance(v, integer_types):
                raise TimeSpecError("by_weekno value must be a number")
            if not (1 <= v <= 53 or -53 <= v <= 1):
                raise TimeSpecError("by_weekno value outside valid range (-53-1 or 1-53)")
            return v
        by_weekno = parse_list('by_weekno', validate_by_weekno)

        def validate_by_setpos(v):
            # XXX: test for exsitence of other by_* values
            if not isinstance(v, integer_types):
                raise TimeSpecError("by_setpos value must be a number")
            return v
        by_setpos = parse_list('by_setpos', validate_by_setpos)

        return cls(
            spans, freq, dt_start, count, until, interval,
            by_month, by_weekday, by_monthday, by_yearday, by_weekno, by_setpos,
        )

    @classmethod
    def from_trusted_spec(cls, spec):
        assert isinstance(spec, dict)
        spans = spec['spans']
        repeat = spec['repeat']
        dt_start = datetime.datetime.strptime(
            spec['start'], "%Y-%m-%d"
        )
        freq = dict(
            daily = rrule.DAILY,
            weekly = rrule.WEEKLY,
            monthly = rrule.MONTHLY,
        )[repeat['freq']]
        interval = repeat.get('interval', 1)
        count = repeat.get('count')
        until = datetime.datetime.strptime(
            repeat['until'], "%Y-%m-%d"
        ) if 'until' in repeat else None
        by_month = repeat.get('by_month')
        by_weekday = [
            (
                rrule.weekday(day[0], day[1])
                if isinstance(day, list)
                else rrule.weekday(day)
            ) for day in repeat['by_weekday']
        ] if 'by_weekday' in repeat else None
        by_monthday = repeat.get('by_monthday')
        by_yearday = repeat.get('by_yearday')
        by_weekno = repeat.get('by_weekno')
        by_setpos = repeat.get('by_setpos')
        return cls(
            spans, freq, dt_start, count, until, interval,
            by_month, by_weekday, by_monthday, by_yearday, by_weekno, by_setpos,
        )

    def __init__(self,
        spans, freq, dt_start, count, until, interval,
        by_month, by_weekday, by_monthday, by_yearday, by_weekno, by_setpos,
    ):
        self._spans = spans
        self._freq = freq
        self._dt_start = dt_start
        self._count = count
        self._until = until
        self._interval = interval
        self._by_month = by_month
        self._by_weekday = by_weekday
        self._by_monthday = by_monthday
        self._by_yearday = by_yearday
        self._by_weekno = by_weekno
        self._by_setpos = by_setpos

        try:
            self._rr = rrule.rrule(
                freq = self._freq,
                until = self._until,
                count = self._count,
                dtstart = self._dt_start,
                interval = self._interval,
                bymonth = self._by_month,
                byweekday = self._by_weekday,
                bymonthday = self._by_monthday,
                byyearday = self._by_yearday,
                byweekno = self._by_weekno,
                bysetpos = self._by_setpos,
                max_year = self._dt_start.year + 25,
            )
        except Exception as err:
            traceback.print_exc()
            raise TimeSpecError("Schedule combination cannot be satisfied")
        first = self._rr.after(datetime.datetime(1, 1, 1))
        if first != self._dt_start:
            raise TimeSpecError("Schedule repeat specification doesn't include start date")

    def serialize(self):
        def encode_dt(dt):
            if dt is None:
                return None
            return dt.strftime("%Y-%m-%d")
        def encode_weekdays(wds):
            if wds is None:
                return None
            return [
                (
                    wd.weekday
                    if wd.n is None
                    else [wd.weekday, wd.n]
                ) for wd in wds
            ]
        repeat = dict(
            count = self._count,
            until = self._until.strftime("%Y-%m-%d") if self._until else None,
            freq = {
                rrule.DAILY: 'daily',
                rrule.WEEKLY: 'weekly',
                rrule.MONTHLY: 'monthly',
            }[self._freq],
            interval = self._interval if self._interval != 1 else None,
            by_month = self._by_month,
            by_weekday = encode_weekdays(self._by_weekday),
            by_monthday = self._by_monthday,
            by_yearday = self._by_yearday,
            by_weekno = self._by_weekno,
            by_setpos = self._by_setpos,
        )
        spec = dict(
            start = self._dt_start.strftime("%Y-%m-%d"),
            repeat = _omit_none(repeat),
            spans = self._spans,
        )
        return spec

    @property
    def min_span_offset(self):
        return self._spans[0][0]

    @property
    def max_span_offset(self):
        return self._spans[-1][1]

    def spans_for(self, occurrence):
        if (
            self._freq == rrule.MONTHLY and
            occurrence.day == 1
        ):
            # For monthly occurences, cap spans to the range of the
            # occurences month, so the spans don't overflow into the
            # next month.
            num_days = monthrange(occurrence.year, occurrence.month)[1]
            month_max_offset = num_days * DAY_MINUTES
            spans = []
            for min_offset, max_offset in self._spans:
                min_offset = min(month_max_offset, min_offset)
                max_offset = min(month_max_offset, max_offset)
                if max_offset - min_offset == 0:
                    continue
                spans.append((min_offset, max_offset))
            return spans
        return self._spans

    @property
    def rr(self):
        return self._rr

    def as_rrule(self):
        return str(self._rr)

    def occurrence_to_spans(self,
        occurrence, tz,
        dt_naive_local_min, dt_naive_local_max=None, until=None,
    ):
        for min_offset, max_offset in self.spans_for(occurrence):
            # print('\nspan: %d:%02d - %d:%02d' % (
            #     min_offset/60, min_offset%60,
            #     max_offset/60, max_offset%60,
            # ))
            dt_naive_local_span_min = occurrence + datetime.timedelta(
                minutes = min_offset,
            )
            if dt_naive_local_max and dt_naive_local_span_min > dt_naive_local_max:
                continue
            if dt_naive_local_span_min < dt_naive_local_min:
                dt_naive_local_span_min = dt_naive_local_min
            # print('naive min: ', dt_naive_local_span_min)

            dt_naive_local_span_max = occurrence + datetime.timedelta(
                minutes = max_offset,
            )
            if dt_naive_local_span_max < dt_naive_local_min:
                continue
            if dt_naive_local_max and dt_naive_local_span_max > dt_naive_local_max:
                dt_naive_local_span_max = dt_naive_local_max
            # print('naive max: ', dt_naive_local_span_max)

            if dt_naive_local_span_min == dt_naive_local_span_max:
                continue
            # print('naive: ', dt_naive_local_span_min, dt_naive_local_span_max)

            dt_local_span_min = schedule_localize(tz, dt_naive_local_span_min).astimezone(tz)
            dt_local_span_max = schedule_localize(tz, dt_naive_local_span_max).astimezone(tz)
            if dt_local_span_min >= dt_local_span_max:
                continue

            # print('local: ', dt_local_span_min, dt_local_span_max)
            # unix_min = dt_to_unix(dt_local_span_min.astimezone(pytz.UTC))
            # unix_max = dt_to_unix(dt_local_span_max.astimezone(pytz.UTC))
            # print('unix: ', unix_min, unix_max, '|||||', (unix_max - unix_min) / 60)

            dt_naive_local_span_min = dt_local_span_min.replace(tzinfo=None)
            dt_naive_local_span_max = dt_local_span_max.replace(tzinfo=None)

            if until:
                if dt_naive_local_span_min > until:
                    continue
                if dt_naive_local_span_max > until:
                    dt_naive_local_span_max = until
                if dt_naive_local_span_min == dt_naive_local_span_max:
                    continue

            yield dt_naive_local_span_min, dt_naive_local_span_max

    def is_exhausted_on(self, tz, dt_naive_local_probe):
        until = self._until + datetime.timedelta(
            days = 1,
        ) if self._until else None

        if until:
            if dt_naive_local_probe > until:
                return True

        dt_naive_local_occurrence_min = dt_naive_local_probe - datetime.timedelta(
            minutes = self.max_span_offset - 1
        )

        occurrences = list(self.rr.xafter(
            dt_naive_local_occurrence_min,
            count = 1, inc = True
        ))

        if not occurrences:
            return True

        for occurrence in occurrences:
            for (
                dt_naive_local_span_min, dt_naive_local_span_max
            ) in self.occurrence_to_spans(
                occurrence, tz,
                dt_naive_local_min = dt_naive_local_probe,
                dt_naive_local_max = None,
                until = until,
            ):
                if dt_naive_local_probe <= dt_naive_local_span_max:
                    return False
        return True

    def active(self, tz, dt_naive_local):
        return bool(self.spans_between(
            tz, dt_naive_local, dt_naive_local + datetime.timedelta(seconds=1)
        ))

    def spans_between(self, tz, dt_naive_local_min, dt_naive_local_max):
        if dt_naive_local_min >= dt_naive_local_max:
            return []

        # print('spans between')
        # print(dt_naive_local_min, dt_naive_local_max)
        dt_naive_local_occurrence_min = dt_naive_local_min - datetime.timedelta(
            minutes = self.max_span_offset
        )
        dt_naive_local_occurrence_max = dt_naive_local_max - datetime.timedelta(
            minutes = self.min_span_offset
        )
        # print('probing between')
        # print(dt_naive_local_occurrence_min, dt_naive_local_occurrence_max)

        occurrences = self.rr.between(
            dt_naive_local_occurrence_min,
            dt_naive_local_occurrence_max,
            inc = True
        )

        until = self._until + datetime.timedelta(
            days = 1,
        ) if self._until else None

        spans = []
        for occurrence in occurrences:
            spans.extend(self.occurrence_to_spans(
                occurrence, tz,
                dt_naive_local_min, dt_naive_local_max, until
            ))
        return spans


if __name__ == "__main__":
    import unittest
    class TestTimeZones(unittest.TestCase):
        def test_all_exist(self):
            for timezone in SUPPORTED_TIMEZONES:
                pytz.timezone(timezone)

    unittest.main()
