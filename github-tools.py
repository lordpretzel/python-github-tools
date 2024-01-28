#!/usr/bin/env python
from ghapi.all import GhApi
import getopt
import sys
import os

def errorExit(message="", e=None):
    print(help)
    if e is None:
        print(message)
    else:
        print("Exception {}\n\n{}\n{}", type(e), e.args, message)
    sys.exit(2)

def readArgs(argv):
    try:
        opts, args = getopt.getopt(argv, "r:u:p:o:f:t:i:T:P:ve:Nc:s:D:H:F:a:", ["repo", "user", "passwd", "organization","forkfrom", "token", "invitee", "Team", "Permission", "private", "email" "nochecks", "clientid", "secret", "description", "homepage", "forkowner", "page"])
        return { key.replace("-",""): value for (key, value) in opts }
    except getopt.GetoptError as e:
        print(opts)
        errorExit(e)

def checkArgs(opts, cmd):
    copts = cmdoptions[cmd]
    if not (("r" in opts and "u" in opts and "p" in opts) or ("t" in opts) or ("c" in opts and "s" in opts)):
        print(f"args: {copts} and {opts}")
        errorExit("need to provide repo, user, and passwd")

def connect(opts):
    token = opts['t'] if 't' in opts else os.environ.get('GITHUB_TOKEN')
    if "t" in opts:
        return GhApi(token=token)

def get_user(opts):
    if "o" in opts:
        return opts['o']
    else:
        return opts['u']

def repoExists(g,user, repo):
    try:
        g.repos.get(user, repo)
        return True
    except Exception:
        return False

def teamExists(g, user, team):
    try:
        g.teams.get_by_name(user, team)
        return True
    except Exception:
        return False

def getTeam(g, user, team):
    return g.teams.get_by_name(user,team)

def userExists(g, user, organization):
    try:
        user = g.orgs.check_membership_for_user(organization, user)
        return user
    except Exception:
        return None

def createTeam(opts,g):
    user = get_user(opts)
    team = opts['T']
    if not teamExists(g, user, team):
        g.teams.create(org=user,name=team)
    if "r" in opts:
        repo = opts['r']
        permission = opts['P']
        g.teams.add_or_update_repo_permissions_in_org(org=user,
                                                      team_slug=team,
                                                      owner=user,
                                                      repo=repo,
                                                      permission=permission)

def inviteUser(opts,g):
    user = get_user(opts)
    repo = opts['r']
    invitee = opts['i']
    permission = opts['P']
    g.repos.add_collaborator(owner=user, repo=repo, username=invitee, permission=permission)

def reinviteFailed(opts,g):
    pass

def inviteToTeam(opts,g):
    user = get_user(opts)
    exists_user = None
    notcheck = True if 'N' in opts else False
    team = opts['T']
    invitee = opts['i']
    role = opts['P'] if 'P' in opts else 'member'

    if (not notcheck) and (not teamExists(g,user,team)):
        errorExit("cannot add using since team {} does not exit".format(opts['T']))
    if not notcheck:
        exists_user = userExists(g, invitee, user)
        print(f"Users exists in org {user}: {exists_user}")
    gteam = getTeam(g,user,team)
    print(f"add role {role} in {team} to {invitee}")
    try:
        g.orgs.create_invitation(org=user,
                                 email=invitee,
                                 role='direct_member',
                                 team_ids=[gteam.id])
    except Exception as e:
        print(e)
    # g.teams.add_or_update_membership_for_user_in_org(
    #     org=user,
    #     team_slug=team,
    #     username=invitee,
    #     role=role)

def listMembers(opts,g):
    users = g.orgs.list_members(
        org=opts['o'],
        role='all' if ('P' not in opts) else opts['P'],
        per_page=100,
        page=1 if 'a' not in opts else opts['a']
        )
    names = [ x['login'] for x in users ]
    print('\n'.join(names))

def changeMemberRole(opts,g):
    g.orgs.set_membership_for_user(org=opts['o'],
                                   username=opts['i'],
                                   role=opts['P'])

def makePrivate(opts,g):
    user = get_user(opts)
    repo = opts['r']
    g.repos.update(owner=user, repo=repo, private=True)

def deleteRepo(opts,g):
    user = get_user(opts)
    repo = opts['r']
    g.repos.delete(user,repo)

def removeUser(opts,g):
    #g.orgs.
    pass

def deleteTeam(opts,g):
    org = opts['o']
    team = opts['T']
    g.teams.delete_in_org(org=org, team_slug=team)

def createRepo(opts,g):
    github_user = get_user(opts)
    is_private = True if 'v' in opts else False
    theowner = opts['F'] if 'F' in opts else github_user
    repo = opts['r']
    desc = opts['D'] if 'D' in opts else None
    homepage = opts['H'] if 'H' in opts else None

    if not repoExists(g, github_user, repo):
        if "f" in opts:
            forkrepo = g.create_fork(owner=theowner,
                                     repo=repo,
                                     organization=github_user)
            #rename: repo.edit(opts['r'])
        else:
            g.repos.create_in_org(org=github_user,
                                name=repo,
                                has_issues=True,
                                private=is_private,
                                description=desc,
                                homepage=homepage)
    if "T" in opts:
        createTeam(opts,g)

def repoExistsCmd(opts,g):
    github_user = get_user(opts)
    repo = opts['r']
    if repoExists(g, github_user, repo):
        print("1")
    else:
        print("0")

commands = {
    "create_repo": createRepo,
    "invite_user": inviteUser,
    "invite_to_team": inviteToTeam,
    "create_team": createTeam,
    "delete_repo": deleteRepo,
    "make_private": makePrivate,
    "delete_team": deleteTeam,
    "remove_user": removeUser,
    "org_change_member_role": changeMemberRole,
    "list_org_members": listMembers,
    "repo_exists": repoExistsCmd
    }

loginopts = [ ['u','p'], ['t'], ['c', 's'] ]

cmdoptions = {
    "create_repo": ['r', "D", "H", "F"] + loginopts,
    "invite_user": ["i", "T"] + loginopts,
    "invite_to_team": ["i", "T"] + loginopts,
    "create_team": ["T", "P"] + loginopts,
    "delete_team": ["T"] + loginopts,
    "remove_user": ["i"] + loginopts,
    "delete_repo": ['r'] + loginopts,
    "make_private": ['r'] + loginopts,
    "list_org_members": ['o', 'a'] + loginopts,
    "org_change_member_role": ['o', 'P', 'i'] + loginopts,
    "repo_exists": ['r', 'u'] + loginopts
    }

help = f"""
github-tools.py COMMAND [-[t]oken accesstoken, [-[c]lientid clientid -[s]ecret clientsecret]] -[r]epo name_of_new_repo -[o]rganization organization_to_use -[f]orkfrom fork_from_here -[t]oken access_token -[i]vitee user_to_invited -[T]eam the_team -[P]ermission repo_permission -[a]Page -[v]private -[D]escription -[H]omepage -[F]orkowner

COMMAND in {','.join( list(commands.keys()) )}
"""

def main():
    if len(sys.argv) <= 3:
        print(len(sys.argv))
        errorExit("need at least a command")
    cmd = sys.argv[1]
    opts = readArgs(sys.argv[2:])
    opts['command'] = cmd
    checkArgs(opts,cmd)
    g = connect(opts)
    commands[cmd](opts,g)

if __name__ == '__main__':
    main()
