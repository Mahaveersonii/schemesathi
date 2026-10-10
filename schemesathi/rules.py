"""Eligibility rule engine: the part of SchemeSathi that never guesses.

Every scheme is a list of checks written from the official eligibility text on myScheme
(the quote is kept next to each check). A check answers True (meets it), False (fails it)
or None (we do not know yet: the person has not told us, or only an office can verify it).

    verdict = "eligible"      every check passed
              "likely"        nothing failed, but something still needs confirming
              "not_eligible"  at least one check failed (the reason is shown)

The AI agent explains these verdicts; it is not allowed to change them.
"""
from dataclasses import dataclass, field

POST_MATRIC = {"class_11_12", "diploma", "undergraduate", "postgraduate"}
COLLEGE = {"undergraduate", "postgraduate"}


@dataclass
class Check:
    label: str                       # plain-language condition
    test: object                     # function(profile) -> True / False / None
    quote: str = ""                  # the official line it comes from


@dataclass
class Scheme:
    slug: str
    name: str
    short: str
    group: str
    benefit: str                     # one-line headline, from the official Benefits section
    yearly_value: int | None = None  # rupees a year we can state with confidence (else None)
    value_note: str = ""
    goal: str = ""                   # the goal it serves (used to rank and to hide off-goal loans)
    checks: list = field(default_factory=list)
    confirm: list = field(default_factory=list)   # things only the office can verify


def _get(p, k):
    v = p.get(k)
    return None if v in ("", None) else v


def age_between(lo, hi=None):
    def t(p):
        a = _get(p, "age")
        return None if a is None else (a >= lo and (hi is None or a <= hi))
    return t


def is_(k, value=True):
    def t(p):
        v = _get(p, k)
        return None if v is None else v == value
    return t


def is_not(k):
    def t(p):
        v = _get(p, k)
        return None if v is None else not v
    return t


def one_of(k, values):
    def t(p):
        v = _get(p, k)
        return None if v is None else v in values
    return t


def at_most(k, limit):
    def t(p):
        v = _get(p, k)
        return None if v is None else v <= limit
    return t


def at_least(k, limit):
    def t(p):
        v = _get(p, k)
        return None if v is None else v >= limit
    return t


def more_than(k, limit):
    def t(p):
        v = _get(p, k)
        return None if v is None else v > limit
    return t


def any_of(*tests):
    """True if any test is True; False only if every test is False."""
    def t(p):
        results = [x(p) for x in tests]
        if any(r is True for r in results):
            return True
        return None if any(r is None for r in results) else False
    return t


def wants(goal):
    def t(p):
        goals = p.get("goals")
        return None if goals is None else goal in goals
    return t


FARMER = one_of("occupation", {"farmer"})
BANK = is_("has_bank_account")
NOT_TAXPAYER = is_not("income_tax_payer")
NOT_GOVT = is_not("govt_employee")
NOT_FORMAL_SS = is_not("formal_social_security")
BPL = is_("bpl")
FEMALE = one_of("gender", {"female"})
SC_ST = one_of("category", {"SC", "ST"})

SCHEMES = [
    # --- Farmers -----------------------------------------------------------
    Scheme("pm-kisan", "Pradhan Mantri Kisan Samman Nidhi", "PM-KISAN", "Farmers",
           "₹6,000 a year, paid in three instalments of ₹2,000", 6000, "₹6,000 a year", "farming",
           [Check("A farmer", FARMER, "All landholding farmers' families"),
            Check("Cultivable land in your own name", is_("land_in_own_name"), "which have cultivable land holding in their names"),
            Check("Not an income-tax payer", NOT_TAXPAYER, "Excluded: all persons who paid income tax in last assessment year"),
            Check("No family member in regular government or PSU service", NOT_GOVT,
                  "Excluded: serving or retired officers and employees of Central/State Government ... PSEs")],
           ["You are not an institutional landholder, constitutional-post holder or practising doctor/engineer/lawyer/CA/architect"]),
    Scheme("pmkmdy", "Pradhan Mantri Kisan Maandhan Yojana", "PM-KMY", "Farmers",
           "Pension of ₹3,000 a month from age 60; the government matches your contribution", None,
           "₹3,000 a month from age 60", "pension",
           [Check("A farmer", FARMER, "The applicant should be a Small or Marginal Farmer"),
            Check("Land in your own name", is_("land_in_own_name"), "whose names appear in the land records"),
            Check("Land up to 2 hectares", at_most("land_hectares", 2), "cultivable landholding up to 2 hectares"),
            Check("Age 18 to 40 when joining", age_between(18, 40), "between 18 and 40 years of age at the time of entry"),
            Check("Has Aadhaar", is_("has_aadhaar"), "should possess an Aadhaar card"),
            Check("Has a savings bank account", BANK, "should have a savings bank account"),
            Check("Not in NPS, ESIC or EPFO", NOT_FORMAL_SS, "Excluded: SMFs covered under NPS, ESIC, EPFO"),
            Check("Not an income-tax payer", NOT_TAXPAYER, "Excluded: all persons who paid income tax"),
            Check("No family member in regular government service", NOT_GOVT, "Excluded: serving or retired officers and employees")],
           ["Your name was in the land records on 01.08.2019"]),
    Scheme("kcc", "Kisan Credit Card", "KCC", "Farmers",
           "Crop loan at 7% a year (up to ₹3 lakh), with 3% extra off for paying on time", None, "", "farming",
           [Check("A farmer, tenant farmer or sharecropper", FARMER, "owner cultivators; tenant farmers, oral lessees & share croppers"),
            Check("Age 18 to 75", age_between(18, 75), "minimum of 18 years of age and be a maximum age of 75 years")]),
    Scheme("pmfby", "Pradhan Mantri Fasal Bima Yojana", "PMFBY", "Farmers",
           "Crop insurance; you pay at most 2% (kharif), 1.5% (rabi) or 5% (commercial crops)", None, "", "farming",
           [Check("A farmer, tenant farmer or sharecropper", FARMER, "All farmers, including tenant farmers and sharecroppers")],
           ["Your crop and area are notified for the season", "You apply within the window, usually 2 weeks from sowing"]),
    # --- Health and insurance ------------------------------------------------
    Scheme("hmdg", "Health Minister's Discretionary Grant", "HMDG", "Health and insurance",
           "Up to ₹50,000 towards treatment in a government hospital", None, "up to ₹50,000 once", "health",
           [Check("Being treated in a government hospital", is_("hospitalised_govt"), "Hospitalized / Undergoing Treatment in a Government Hospital"),
            Check("Family income up to ₹1 lakh a year", at_most("annual_family_income", 100000), "must not exceed ₹1,00,000/- per annum"),
            Check("Not a central or state government employee", NOT_GOVT, "must not be an employee of either Central or State Govt")]),
    Scheme("nikshay", "Nikshay Poshan Yojana", "Nikshay Poshan", "Health and insurance",
           "₹1,000 a month for nutrition during TB treatment", 12000, "₹1,000 a month during treatment", "health",
           [Check("Being treated for tuberculosis (TB)", is_("tb_patient"), "All patients with tuberculosis (TB) who are notified")],
           ["You are registered on the NIKSHAY portal (your TB centre does this)"]),
    Scheme("pmjjby", "Pradhan Mantri Jeevan Jyoti Bima Yojana", "PMJJBY", "Health and insurance",
           "₹2 lakh life cover for a premium of ₹436 a year", None, "", "insurance",
           [Check("Age 18 to 50", age_between(18, 50), "must be between 18 to 50 Years"),
            Check("Has a bank or post-office account", BANK, "must hold an individual bank / post office account")]),
    Scheme("pmsby", "Pradhan Mantri Suraksha Bima Yojana", "PMSBY", "Health and insurance",
           "₹2 lakh accident cover for a premium of ₹20 a year", None, "", "insurance",
           [Check("Age 18 to 70", age_between(18, 70), "aged between 18 years (completed) and 70 years"),
            Check("Has a bank account", BANK, "Individual bank account holders of participating banks")]),
    # --- Housing and household -------------------------------------------------
    Scheme("pmay-u", "Pradhan Mantri Awas Yojana - Urban", "PMAY-U", "Housing and household",
           "Help to build or buy a pucca house in a town or city (EWS, LIG and MIG families)", None, "", "housing",
           [Check("Lives in a town or city", one_of("area", {"urban"}), "The town/city in which the family resides must be covered"),
            Check("Family income up to ₹18 lakh a year", at_most("annual_family_income", 1800000), "MIG-2: between ₹12,00,001 and ₹18,00,000"),
            Check("No pucca house anywhere in India", is_not("owns_pucca_house"), "must not be owning a pucca house in any part of the country")],
           ["Your town is covered under PMAY-U", "Your family has not used another central housing scheme before"]),
    Scheme("pmay-g", "Pradhan Mantri Awaas Yojana - Gramin", "PMAY-G", "Housing and household",
           "₹1.2 lakh (₹1.3 lakh in hilly areas) to build a house, plus up to ₹12,000 for a toilet", None,
           "₹1.2–1.3 lakh once", "housing",
           [Check("Lives in a village", one_of("area", {"rural"}), "houseless households living in zero, one, or two-room houses"),
            Check("No pucca house", is_not("owns_pucca_house"), "kutcha walls and kutcha roofs")],
           ["Your household is on the SECC 2011 / Awaas+ list, verified by the Gram Sabha"]),
    Scheme("pmuy", "Pradhan Mantri Ujjwala Yojana", "PMUY", "Housing and household",
           "Free LPG connection, first refill and stove", None, "", "household",
           [Check("A woman", FEMALE, "An adult woman ... Male Member from a household cannot apply"),
            Check("Aged 18 or more", age_between(18), "An adult woman"),
            Check("No LPG connection in the household", is_not("has_lpg_connection"), "not having an LPG connection in her household"),
            Check("Poor household (BPL, SC/ST or 14-point declaration)", any_of(BPL, SC_ST),
                  "SECC 2011 list, SC/ST households ... or 14-point declaration")]),
    Scheme("pmjdy", "Pradhan Mantri Jan Dhan Yojana", "PMJDY", "Housing and household",
           "Zero-balance bank account, RuPay card with ₹2 lakh accident cover, ₹10,000 overdraft", None, "", "banking",
           [Check("An Indian citizen aged 10 or more", age_between(10), "The applicant should be an Indian National"),
            Check("Does not yet have a bank account", is_not("has_bank_account"), "Most useful for people without an account")]),
    # --- Entrepreneurs and workers ------------------------------------------------
    Scheme("pmmy", "Pradhan Mantri Mudra Yojana", "MUDRA", "Entrepreneurs and workers",
           "Business loans: up to ₹50,000 (Shishu), ₹5 lakh (Kishore), ₹10 lakh (Tarun), ₹20 lakh (Tarun Plus)", None, "", "business",
           [Check("Wants to start or grow a small business", wants("business"), "to signify the stage of growth ... of the micro unit"),
            Check("Not a loan defaulter", is_not("loan_defaulter"), "should not be a defaulter to any bank")]),
    Scheme("pm-svanidhi", "PM Street Vendor's AtmaNirbhar Nidhi", "PM SVANidhi", "Entrepreneurs and workers",
           "Collateral-free working-capital loan of ₹10,000, then ₹20,000 and ₹50,000, with 7% interest subsidy", None, "", "business",
           [Check("A street vendor", one_of("occupation", {"street_vendor"}), "Street vendors in possession of Certificate of Vending")],
           ["You hold a vending certificate, or a Letter of Recommendation from your urban local body"]),
    Scheme("sui", "Stand-Up India", "Stand-Up India", "Entrepreneurs and workers",
           "Bank loan of ₹10 lakh to ₹1 crore for a new enterprise", None, "", "business",
           [Check("Wants to start a business", wants("business"), "Finance is provided for Greenfield Enterprises"),
            Check("A woman, or from SC/ST", any_of(FEMALE, SC_ST), "If the applicant is a male, he must be from SC / ST category"),
            Check("Aged 18 or more", age_between(18), "at least 18 years"),
            Check("Not a loan defaulter", is_not("loan_defaulter"), "must not be in default to any bank")],
           ["It is a new (greenfield) enterprise"]),
    Scheme("pmegp", "Prime Minister's Employment Generation Programme", "PMEGP", "Entrepreneurs and workers",
           "Subsidy of 15–35% of the project cost to set up a new micro-enterprise", None, "", "business",
           [Check("Wants to start a business", wants("business"), "for setting up new micro-enterprises"),
            Check("Aged 18 or more", age_between(18), "Any individual, above 18 years of age")],
           ["For projects above ₹10 lakh (manufacturing) or ₹5 lakh (service) you need Class 8 pass"]),
    Scheme("pmv", "PM Vishwakarma", "PM Vishwakarma", "Entrepreneurs and workers",
           "₹15,000 toolkit, ₹500 a day training stipend, loans of ₹1 lakh + ₹2 lakh at 5%", None, "", "business",
           [Check("A traditional artisan or craftsperson", one_of("occupation", {"artisan"}), "artisan or craftsperson working with hands and tools"),
            Check("Aged 18 or more", age_between(18), "minimum age of the applicant should be 18 years"),
            Check("No PMEGP / SVANidhi / Mudra loan in the last 5 years", is_not("prior_govt_business_loan"), "should not have availed loans under similar credit-based schemes ... in the past 5 years"),
            Check("No family member in government service", NOT_GOVT, "A person in government service and their family members shall not be eligible")],
           ["Your trade is one of the 18 listed family-based trades"]),
    Scheme("pm-sym", "Pradhan Mantri Shram Yogi Maan-dhan", "PM-SYM", "Entrepreneurs and workers",
           "Pension of ₹3,000 a month from age 60; the government matches your contribution", None,
           "₹3,000 a month from age 60", "pension",
           [Check("An unorganised worker", one_of("occupation", {"unorganised_worker", "street_vendor", "artisan", "farm_labourer"}),
                  "unorganized worker, construction workers, domestic workers, cobbler etc."),
            Check("Age 18 to 40 when joining", age_between(18, 40), "entry age between 18 and 40 years"),
            Check("Own income up to ₹15,000 a month", at_most("monthly_income", 15000), "monthly income of ₹15,000/- or less"),
            Check("Has a savings bank account", BANK, "must possess a Savings Bank Account"),
            Check("Not an income-tax payer", NOT_TAXPAYER, "must not be an income tax payer"),
            Check("Not in EPFO, NPS or ESIC", NOT_FORMAL_SS, "must not be holding membership in EPFO / NPS / ESIC")]),
    Scheme("mgnrega", "Mahatma Gandhi National Rural Employment Guarantee Act", "MGNREGA", "Entrepreneurs and workers",
           "At least 100 days of paid work a year, within 15 days of asking", None, "", "work",
           [Check("Aged 18 or more", age_between(18), "at least 18 years of age"),
            Check("Lives in a village", one_of("area", {"rural"}), "must be residing in a Rural Area")]),
    # --- Pensions --------------------------------------------------------------
    Scheme("apy", "Atal Pension Yojana", "APY", "Pensions",
           "Pension of ₹1,000 to ₹5,000 a month from age 60", None, "₹1,000–5,000 a month from age 60", "pension",
           [Check("Age 18 to 40 when joining", age_between(18, 40), "minimum age of joining APY is 18 years and maximum is 40 years"),
            Check("Has a savings bank account", BANK, "auto-debit ... from the savings bank account"),
            Check("Not an income-tax payer", NOT_TAXPAYER, "any citizen who is or has been an income tax payer, shall not be eligible")]),
    Scheme("nsap-ignoaps", "Indira Gandhi National Old Age Pension Scheme", "IGNOAPS", "Pensions",
           "₹200 a month (₹500 from age 80)", 2400, "₹2,400 a year (₹6,000 from age 80)", "pension",
           [Check("Aged 60 or more", age_between(60), "at least 60 years of age"),
            Check("Below the poverty line (BPL)", BPL, "should be living Below Poverty Line")]),
    Scheme("ignwps", "Indira Gandhi National Widow Pension Scheme", "IGNWPS", "Pensions",
           "Monthly widow pension, paid through your state", None, "amount set by your state (not stated on myScheme)", "pension",
           [Check("A widow", is_("widow"), "must be a widow"),
            Check("Age 40 to 79", age_between(40, 79), "in the age group of 40-79 years"),
            Check("Below the poverty line (BPL)", BPL, "household living below the poverty line")]),
    Scheme("igndps", "Indira Gandhi National Disability Pension Scheme", "IGNDPS", "Pensions",
           "₹300 a month (₹500 from age 80)", 3600, "₹3,600 a year", "pension",
           [Check("Aged 18 or more", age_between(18), "18 years and above"),
            Check("Disability above 80%", more_than("disability_percent", 80), "disability should be more than 80%"),
            Check("Below the poverty line (BPL)", BPL, "should belong to the Below Poverty Line")]),
    # --- Women and children ------------------------------------------------------
    Scheme("pmmvy", "Pradhan Mantri Matru Vandana Yojana", "PMMVY", "Women and children",
           "₹5,000 for the first child (₹6,000 for a second child if it is a girl)", None, "₹5,000 once", "health",
           [Check("Pregnant", is_("pregnant"), "a pregnant women"),
            Check("Aged 19 or more", age_between(19), "at least 19 years old"),
            Check("First child (or second, if a girl)", is_("first_child"), "applicable only for the first live birth"),
            Check("From a listed disadvantaged group (SC/ST, BPL, 40%+ disability or income under ₹8 lakh)",
                  any_of(SC_ST, BPL, at_least("disability_percent", 40), at_most("annual_family_income", 799999)),
                  "Women whose net family income is less than Rs. 8 Lakh per annum"),
            Check("Not in regular government or PSU employment", NOT_GOVT, "in regular employment with the Central Government or State Government or PSU")]),
    Scheme("jssk", "Janani Shishu Suraksha Karyakram", "JSSK", "Women and children",
           "Free delivery (including C-section), medicines, tests, food and transport in government facilities", None, "", "health",
           [Check("Pregnant", is_("pregnant"), "must be a pregnant woman")],
           ["You deliver in a government health facility"]),
    Scheme("jsy1", "Janani Suraksha Yojana", "JSY", "Women and children",
           "Cash for institutional delivery: ₹1,400 rural / ₹1,000 urban in low-performing states", None, "up to ₹1,400 once", "health",
           [Check("Pregnant", is_("pregnant"), "must be a pregnant woman"),
            Check("BPL or SC/ST (all women qualify in low-performing states)", any_of(BPL, SC_ST),
                  "High Performing States: must be from a BPL household ... SC/ST woman")],
           ["You deliver in a government or accredited private health facility"]),
    # --- Students and youth ------------------------------------------------------
    Scheme("csss-cus", "PM-USP Central Sector Scheme of Scholarship", "PM-USP CSSS", "Students and youth",
           "₹12,000 a year at graduation, ₹20,000 at post-graduation", 12000, "₹12,000–20,000 a year", "education",
           [Check("In a regular college degree (UG or PG)", one_of("student_level", COLLEGE), "must be pursuing regular degree courses"),
            Check("Above the 80th percentile in Class 12", is_("class12_top20"), "above the 80th percentile of successful candidates"),
            Check("Family income up to ₹4.5 lakh a year", at_most("annual_family_income", 450000), "should not exceed ₹4,50,000/- per annum"),
            Check("Not receiving another scholarship", is_not("other_scholarship"), "already availing the benefit from any other scholarship ... not eligible")]),
    Scheme("pm-yasasvipmsobcebcdnts", "PM-YASASVI Post-Matric Scholarship (OBC, EBC, DNT)", "PM-YASASVI", "Students and youth",
           "Up to ₹20,000 a year (tuition + academic allowance)", 20000, "up to ₹20,000 a year", "education",
           [Check("OBC, EBC or DNT", one_of("category", {"OBC", "EBC", "DNT"}), "belonging to OBCs, EBCs, and DNTs"),
            Check("Studying after Class 10", one_of("student_level", POST_MATRIC), "recognized post-matriculation or post-secondary courses"),
            Check("Family income up to ₹2.5 lakh a year", at_most("annual_family_income", 250000), "does not exceed ₹2.50 lakhs per annum"),
            Check("Not holding another scholarship", is_not("other_scholarship"), "will not hold any other scholarship/stipend")]),
    Scheme("post-dis", "Post-Matric Scholarship for Students with Disabilities", "Post-Matric (Disability)", "Students and youth",
           "Maintenance allowance and fees for studies after Class 10", None, "", "education",
           [Check("Studying after Class 10", one_of("student_level", POST_MATRIC), "pursuing a post-matric qualification"),
            Check("Disability of 40% or more", at_least("disability_percent", 40), "disability percentage of 40% or above"),
            Check("Parents' income up to ₹2.5 lakh a year", at_most("annual_family_income", 250000), "must not exceed ₹ 2.50 Lakh per Annum"),
            Check("Not receiving another government scholarship", is_not("other_scholarship"), "must not be availing any other scholarship")]),
    Scheme("naps", "National Apprenticeship Promotion Scheme", "NAPS-2", "Students and youth",
           "Paid apprenticeship; the government adds 25% of the stipend, up to ₹1,500 a month", 18000, "up to ₹18,000 a year", "skills",
           [Check("Wants a job or training", wants("skills"), "transition from academia to workplace"),
            Check("Age 14 to 35", age_between(14, 35), "upper age limit should be 35 years")]),
    Scheme("pmkvy-stt", "Pradhan Mantri Kaushal Vikas Yojana - Short Term Training", "PMKVY", "Students and youth",
           "Free short-term skill training with a certificate", None, "", "skills",
           [Check("Wants a job or training", wants("skills"), "skill training"),
            Check("Age 15 to 45", age_between(15, 45), "aged between 15-45 years"),
            Check("Has Aadhaar", is_("has_aadhaar"), "possesses an Aadhaar card"),
            Check("Has an Aadhaar-linked bank account", BANK, "an Aadhaar linked bank account")]),
    Scheme("sl", "Skill Loan Scheme", "Skill Loan", "Students and youth",
           "Loan of up to ₹1.5 lakh for an ITI, polytechnic, college or skill course", None, "", "skills",
           [Check("Wants a job or training", wants("skills"), "secured admission in a course"),
            Check("Has a course admission", is_("has_course_admission"), "has secured admission in a course run by ITIs, Polytechnics ...")]),
]

BY_SLUG = {s.slug: s for s in SCHEMES}
GOALS = {"farming": "Farming", "health": "Health and medical", "insurance": "Insurance", "housing": "A house",
         "household": "Cooking gas", "banking": "A bank account", "business": "Start or grow a business",
         "work": "Paid work", "pension": "Pension and old age", "education": "Education and scholarships",
         "skills": "Job training"}
GOAL_GATED = {"business", "skills"}   # schemes that only make sense if you want them

# Life situations: a scheme built on one of these is not "likely" just because we were not told.
# Unless the person says it applies, the scheme is shown as "only if this applies to you".
SITUATIONS = {"Pregnant", "A widow", "Being treated for tuberculosis (TB)", "Being treated in a government hospital",
              "Has a course admission", "Studying after Class 10", "In a regular college degree (UG or PG)",
              "Disability above 80%", "Disability of 40% or more"}


def evaluate(profile: dict) -> list[dict]:
    """Run every scheme's checks against one person. Returns one result per scheme."""
    out = []
    profile = dict(profile)
    if profile.get("gender") == "male":
        profile.setdefault("pregnant", False)   # maternity schemes; the widow pension is for women
        profile.setdefault("widow", False)
    goals = set(profile.get("goals") or [])
    for s in SCHEMES:
        passed, failed, unknown, only_if = [], [], [], []
        off_goal = False
        for c in s.checks:
            r = c.test(profile)
            if c.label.startswith("Wants") and r is False:
                off_goal = True          # not wanting a loan is not the same as being ineligible
                continue
            if r is None and c.label in SITUATIONS:
                only_if.append(c.label)  # e.g. a maternity scheme for someone who did not say they are pregnant
            (passed if r is True else failed if r is False else unknown).append({"label": c.label, "quote": c.quote})
        verdict = "not_eligible" if failed else ("likely" if unknown or s.confirm else "eligible")
        out.append({
            "slug": s.slug, "name": s.name, "short": s.short, "group": s.group, "benefit": s.benefit,
            "yearly_value": s.yearly_value, "value_note": s.value_note, "goal": s.goal,
            "verdict": verdict, "passed": passed, "failed": failed, "unknown": unknown, "confirm": s.confirm,
            "relevant": not off_goal and not only_if, "only_if": only_if,
            "url": f"https://www.myscheme.gov.in/schemes/{s.slug}",
        })
    order = {"eligible": 0, "likely": 1, "not_eligible": 2}
    out.sort(key=lambda r: (order[r["verdict"]] if r["relevant"] or r["verdict"] == "not_eligible" else 1.5,
                            not (r["goal"] in goals), -(r["yearly_value"] or 0)))
    return out


def summary(results: list[dict]) -> dict:
    """Counts the schemes that fit this person (relevant ones); off-goal and 'only if' schemes are listed apart."""
    ok = [r for r in results if r["verdict"] == "eligible" and r["relevant"]]
    maybe = [r for r in results if r["verdict"] == "likely" and r["relevant"]]
    return {"eligible": len(ok), "likely": len(maybe),
            "not_eligible": sum(r["verdict"] == "not_eligible" for r in results),
            "other": sum(r["verdict"] != "not_eligible" and not r["relevant"] for r in results),
            "yearly_cash": sum(r["yearly_value"] or 0 for r in ok + maybe)}
