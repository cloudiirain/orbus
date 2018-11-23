#!/usr/bin/python
"""Read a Dungeon Archive .tsv file to generate achievements."""

import dataset
import datetime
import sys


class QuestReport(object):
    """Represents a single Quest Report."""

    def __init__(self, row):
        """Construct a Quest Report from a .tsv row."""
        try:
            self.uid = int(row[0])
            self.version = row[1]
            self.date = row[2]
            self.player = row[3]
            self.character = row[4]
            self.party = row[5]
            self.depth = int(row[6])
            self.dive = int(row[7])
            self.days = int(row[8])
            self.hp = int(row[9].split("/")[0])
            self.karma = row[10]
            self.wc = int(row[11])
            self.url = row[12]
            self.lastContext = row[13]
            self.nextRoll = row[14]
            self.nextDmg = row[15]
            self.nextContext = row[16]
        except:
            pass


def makeDb(filename):
    """Construct a database of Quest Reports from a .tsv file.

    Args:
        filename (str): Filename of the .tsv file.

    Returns:
        A dataset table object.

    """
    c = dataset.connect('sqlite:///:memory:')
    table = c['quest_reports']
    with open(filename) as f:
        # We skip the first row as it contains the header
        for line in f.readlines()[1:]:
            row = line.strip().split("\t")
            r = QuestReport(row)
            table.insert(vars(r))
    return table


def run(filename):
    """Run main method."""
    db = makeDb(filename)
    chars = list(_['character'] for _ in db.distinct('character'))

    # Make a character dictionary
    charDict = {}
    for char in chars:
        reports = list(db.find(character=char))
        charDict[char] = {
            'reports': reports,
            'status': reports[-1]['nextContext'],
            'maxDepth': 0,
            'player': reports[0]['player']
        }
        for report in reports:
            if report['depth'] > charDict[char]['maxDepth']:
                charDict[char]['maxDepth'] = report['depth']

    # Dungeon Statistics
    print '[B][SIZE=5]Orbus Dungeon Statistics[/SIZE][/B]'
    nQuests = db.count()
    maxDepth = db.find_one(order_by='-depth')['depth']
    nChars = len(chars)
    nDead = db.count(nextContext="DEATH") + db.count(nextContext="QUIT")
    nRetired = db.count(nextContext="RETIRE")
    print '[list]'
    print '[*][B][U]Total Quest Reports[/U][/B]: {}'.format(nQuests)
    print '[*][B][U]Total Adventurers[/U][/B]: {}'.format(nChars)
    print '[list]'
    print '[*][B][U]Total Active[/U][/B]: {}'.format(nChars - nDead - nRetired)
    print '[*][B][U]Retired Veterans[/U][/B]: {}'.format(nRetired)
    print '[*][B][U]Total Dead/MIA[/U][/B]: {}'.format(nDead)
    print '[/list]'
    print '[/list]\n'

    # Deepest Diver
    print '[B][SIZE=5]Leaderboard: Deepest Divers[/SIZE][/B]'
    print '[I][SIZE=3]The top 3 deepest dives in the Orbus Dungeon.[/SIZE][/I]'
    for char, r in sorted(charDict.items(), key=lambda x: x[1]['maxDepth'], reverse=True)[0:3]:  # noqa
        print '[spoiler="{} ({}) - {} meters"]'.format(
            char, r['player'], r['maxDepth']
        )
        print '[list]'
        for step in r['reports']:
            print '[*][B]Day {} ({} HP)[/B]: [URL={}]{} Meters[/URL] (Roll: {}) - {}'.format(  # noqa
                step['days'], step['hp'], step['url'], step['depth'],
                step['nextRoll'], step['nextContext']
            )
        print '[/list]'
        print '[/spoiler]'
    print ''

    # Living Legends
    print '[B][SIZE=5]Leaderboard: Living Legends[/SIZE][/B]'
    print '[I][SIZE=3]Top 3 retirees who braved the dungeon and survived to tell the tale.[/SIZE][/I]'  # noqa
    retireDict = {k: v for k, v in charDict.iteritems() if 'RETIRE' in v['status']}  # noqa
    for char, r in sorted(retireDict.items(), key=lambda x: x[1]['maxDepth'], reverse=True)[0:3]:  # noqa
        print '[spoiler="{} ({}) - {} meters - {} HP remaining"]'.format(
            char, r['player'], r['maxDepth'], r['reports'][-1]['hp']
        )
        print '[list]'
        for step in r['reports']:
            print '[*][B]Day {} ({} HP)[/B]: [URL={}]{} Meters[/URL] (Roll: {}) - {}'.format(  # noqa
                step['days'], step['hp'], step['url'], step['depth'],
                step['nextRoll'], step['nextContext']
            )
        print '[/list]'
        print '[/spoiler]'
    print ''

    # Longest Lived
    print '[B][SIZE=5]Leaderboard: Longest Lived[/SIZE][/B]'
    print '[I][SIZE=3]The top 3 survival runs in the Orbus Dungeon.[/SIZE][/I]'
    for char, r in sorted(charDict.items(), key=lambda x: len(x[1]['reports']), reverse=True)[0:3]:  # noqa
        print '[spoiler="{} ({}) - {} Quest Reports"]'.format(
            char, r['player'], len(r['reports'])
        )
        print '[list=1]'
        for step in r['reports']:
            print '[*][B]Day {} ({} HP)[/B]: [URL={}]{} Meters[/URL] (Roll: {}) - {}'.format(  # noqa
                step['days'], step['hp'], step['url'], step['depth'],
                step['nextRoll'], step['nextContext']
            )
        print '[/list]'
        print '[/spoiler]'
    print ''

    # Cautionary Tales
    print '[B][SIZE=5]Cautionary Tales[/SIZE][/B]'
    depths = sorted(_['depth'] for _ in db.distinct('depth'))
    for depth in depths:
        hurtReports = list(db.find(lastContext='HURT', depth=depth, order_by='hp', _limit=10))  # noqa
        if len(hurtReports) > 0:
            print '[spoiler="{} Meters"]'.format(depth)
            print '[list]'
            for report in hurtReports:
                print '[*][B]{} (@{})[/B]: [URL={}]{} HP Remaining[/URL]'.format(  # noqa
                    report['character'], report['player'], report['url'],
                    report['hp']
                )
            print '[/list]'
            print '[/spoiler]'


if __name__ == '__main__':
    date = datetime.datetime.today().strftime('%m-%d-%Y')
    print '[B][SIZE=6]Orbus Guild Achievements[/SIZE][/B]'
    print 'Last updated on: {}.\n'.format(date)
    print '[CENTER][B][URL="https://docs.google.com/document/d/1Fhf895mETdZ8RjlRRrYIf9NfoNbmntS7pEU_3ZD8vW4/edit?usp=sharing"][SIZE=6]CLICK HERE FOR THE HALL OF FAME (GOOGLE DOCS)[/SIZE][/URL][/B][/CENTER]\n'
    run(sys.argv[1])
    print '\n[CENTER][B][URL="https://docs.google.com/spreadsheets/d/1eK9bA9hci_TLuzA6u8lmSHcM92mODq_ehQ1NM6G2ITU/edit?usp=sharing"][SIZE=3]CLICK HERE TO CONTRIBUTE TO THE LEADERBOARD (GOOGLE SHEETS)[/SIZE][/URL][/B][/CENTER]\n'
