"""
Template. The live file is data/work/storm_openers.py and is never committed.

Every weekday the Outreach Desk task rewrites the live copy with the morning's verified severe
weather and the verification notes for that day's queue. build_desk.py loads data/work first and
falls back to this file, so a fresh clone runs with the storm tab simply empty.

Why it is not committed: STORM_DM and VERIFY name real people and describe their employers'
portfolios. Why it is not in the monthly plan either: a storm trigger is worth days, not weeks, so
it is applied at build time and expires on its own.

Rules that the generating task must hold to, and that a reviewer should check:
  - every event carries a source URL, and it is a primary weather source wherever one exists
  - no claim that any specific property was damaged
  - no claim outcome, no deductible language, no pricing (Sales Brain trust boundary)
  - nothing about new construction, including topping-out news, which is a new roof on a new
    building and therefore not Hustad's work

Shape:

    DESK_DATE = '2026-08-27'          # the day this file was built; the desk shows the storm tab
                                      # only when it matches the day being rendered

    EVENTS = [
     {'id':'CHI-0727', 'date':'2026-07-27', 'where':'Chicago metro',
      'what':'7 tornadoes, 104 mph gust at Monee, hail near 3 inches',
      'src':'https://www.weather.gov/lot/2026_07_27_severe_flood'},
    ]

    # target_id -> (event ids behind it, the alternate first touch)
    STORM_DM = {
     'T016': (['CHI-0727'], \"\"\"Hi Jordan,

    Two of your four states took damaging wind this month...

    Want a sample of that post-event condition read?\"\"\"),
    }

    # target_id -> (status, what was checked, what the live trigger is)
    # status: clean | revised | flagged | no-trigger
    VERIFY = {
     'T016': ('clean', 'Portfolio count confirmed on their own site; nothing fresher since April.',
              'Three of four states hit in 16 days. Strongest trigger on the list.'),
    }
"""
DESK_DATE = ''
EVENTS = []
STORM_DM = {}
VERIFY = {}
