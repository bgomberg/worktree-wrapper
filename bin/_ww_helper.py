#!/usr/bin/env python

import argparse
import json
import os
import shutil
import subprocess
import sys


HOME_PATH = os.path.expanduser('~')
TEMP_FILE_PATH = os.path.join(HOME_PATH, '.wwtmp')
WW_BASE_PATH = os.path.join(HOME_PATH, '.ww')
CONFIG_FILE_PATH = os.path.join(HOME_PATH, '.wwconfig')
CONFIG_VERSION = 1
DEFAULT_CONFIG = {
    '_version': CONFIG_VERSION,
    'repos': {},
    'active_repo': None,
}


class WorktreeWrapper:
    def __init__(self):
        # create the base path if it doesn't exist
        if not os.path.exists(WW_BASE_PATH):
            os.mkdir(WW_BASE_PATH)
        # load the configuration data
        try:
            with open(CONFIG_FILE_PATH, 'r+') as f:
                self._config = json.load(f)
        except (IOError, ValueError) as e:
            # either the file exists or isn't valid, so just use the defaults
            self._config = DEFAULT_CONFIG
        if self._config['_version'] != CONFIG_VERSION:
            # if the versions don't match, just reset the config to the defaults for now
            # TODO: support version upgrades
            self._config = DEFAULT_CONFIG
        # create the temp file
        self._temp_file = open(TEMP_FILE_PATH, 'w')

    def __del__(self):
        self._temp_file.close()
        with open(CONFIG_FILE_PATH, 'w') as f:
            f.write(json.dumps(self._config, sort_keys=True, indent=4) + '\n')

    def _abort(self, msg):
        print 'ERROR: ' + msg
        sys.exit(1)

    def _get_repo_from_args(self, args):
        if not args.repo:
            if not self._config['active_repo']:
                self._abort('No repo specified and no active repo')
            repo = self._config['active_repo']
        else:
            repo = args.repo
        if repo not in self._config['repos']:
            self._abort('Repo does not exist')
        return repo

    def _repo_command(self, repo_path, cmd, print_output=True):
        cwd = os.getcwd()
        os.chdir(repo_path)
        try:
            output = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            self._abort('Internal error: cmd failed (%s) with error (%s)' % (cmd, str(e)))
        os.chdir(cwd)
        if print_output:
            print output.strip()
        return output

    def _repo_command_num_lines(self, repo_path, cmd):
        return int(self._repo_command(repo_path, cmd + ' | wc -l', print_output=False))

    def _add_tmp_script_line(self, line):
        self._temp_file.write(line + '\n')

    def repo_list_cmd(self, args):
        if not self._config['repos']:
            return
        name_width = max(len(x) for x in self._config['repos'].keys())
        for name, info in self._config['repos'].items():
            active_repo_char = '*' if name == self._config['active_repo'] else ' '
            print '%s %-*s  %s' % (active_repo_char, name_width, name, info['repo'])

    def repo_add_cmd(self, args):
        if args.name in self._config['repos']:
            self._abort('Repo already exists')
        if not os.path.exists(args.path):
            self._abort('Repo path does not exist')
        base_path = os.path.join(WW_BASE_PATH, args.name)
        if os.path.exists(base_path):
            self._abort('Internal error: base path already exists')
        os.mkdir(base_path)
        self._config['repos'][args.name] = {
            'repo': os.path.abspath(args.path),
            'base': base_path,
        }

    def repo_rm_cmd(self, args):
        if args.name not in self._config['repos']:
            self._abort('Repo does not exist')
        shutil.rmtree(self._config['repos'][args.name]['base'])
        del self._config['repos'][args.name]

    def repo_set_active_cmd(self, args):
        if args.name not in self._config['repos']:
            self._abort('Repo does not exist')
        self._config['active_repo'] = args.name

    def new_cmd(self, args):
        repo = self._get_repo_from_args(args)
        repo_info = self._config['repos'][repo]
        wt_path = os.path.join(repo_info['base'], args.name)
        cmd = 'git worktree add "%s" -b "%s"' % (wt_path , args.name)
        self._repo_command(repo_info['repo'], cmd)

    def rm_cmd(self, args):
        repo = self._get_repo_from_args(args)
        repo_info = self._config['repos'][repo]
        wt_path = os.path.join(repo_info['base'], args.name)
        if not os.path.exists(wt_path):
            self._abort('Worktree does not exist')
        if not args.force:
            # make sure the working tree is completely clean
            if self._repo_command_num_lines(wt_path, 'git status --porcelain') != 0:
                self._abort('Working tree is not clean (override with "-f")')
            # make sure the branch is merged by checking how many branches contain the HEAD commit
            num_branches = self._repo_command_num_lines(wt_path, 'git branch -a --contains HEAD')
            if num_branches == 0:
                self._abort('Internal error: No branches contain HEAD commit')
            elif num_branches == 1:
                self._abort('Branch is not merged (override with "-f")')
        # remove the directory
        shutil.rmtree(wt_path)
        # remove the worktree from git's metadata
        self._repo_command(repo_info['repo'], 'git worktree prune')
        # remove the branch
        del_flag = '-D' if args.force else '-d'
        self._repo_command(repo_info['repo'], 'git branch %s %s' % (del_flag, args.name))
        if self._config['active_repo'] == repo:
            self._config['active_repo'] = None

    def ls_cmd(self, args):
        repo = self._get_repo_from_args(args)
        repo_info = self._config['repos'][repo]
        output = self._repo_command(repo_info['repo'], 'git worktree list --porcelain',
                                    print_output=False)
        temp = [x.split('\n') for x in output.strip().split('\n\n')]
        temp = [dict([tuple(x.split(' ')) for x in y]) for y in temp]
        worktrees = []
        for info in temp:
            worktree_path = os.path.normpath(info['worktree'])
            repo_base, worktree_name = os.path.split(worktree_path)
            if os.path.normpath(repo_base) != os.path.normpath(repo_info['base']):
                continue
            commit = info['HEAD'][:7]
            branch = info['branch'].split('/')[-1]
            worktrees.append((worktree_name, worktree_path, commit, branch))
        name_width = max(len(x[0]) for x in worktrees)
        path_width = max(len(x[1]) for x in worktrees)
        for name, path, commit, branch in worktrees:
            print "%-*s  %-*s  %s [%s]" % (name_width, name, path_width, path, commit, branch)

    def cd_cmd(self, args):
        repo = self._get_repo_from_args(args)
        worktree_path = os.path.join(self._config['repos'][repo]['base'], args.name)
        if not os.path.exists(worktree_path):
            self._abort('Worktree not found')
        # make the path relative to $HOME so it works well on Windows (with MinGW)
        worktree_path_rel = os.path.relpath(worktree_path, HOME_PATH).replace('\\', '\\\\')
        self._add_tmp_script_line('cd $HOME/%s' % (worktree_path_rel))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='ww')
    subparsers = parser.add_subparsers()

    # "repo" subcommand
    parser_repo = subparsers.add_parser('repo', help='manage the known repos')
    subparsers_repo = parser_repo.add_subparsers()

    # "repo list" subcommand
    parser_repo_list = subparsers_repo.add_parser('ls', help='list all the known repos')
    parser_repo_list.set_defaults(func='repo_list_cmd')

    # "repo add" subcommand
    parser_repo_add = subparsers_repo.add_parser('add', help='add a new repo')
    parser_repo_add.set_defaults(func='repo_add_cmd')
    parser_repo_add.add_argument('name', type=str, help='name to assign to the repo')
    parser_repo_add.add_argument('path', type=str, help='path to the repo')

    # "repo rm" subcommand
    parser_repo_rm = subparsers_repo.add_parser('rm', help='removes a repo')
    parser_repo_rm.set_defaults(func='repo_rm_cmd')
    parser_repo_rm.add_argument('name', type=str, help='name of the repo')

    # "repo set-active" subcommand
    parser_repo_set_active = subparsers_repo.add_parser('set-active', help='sets the active repo')
    parser_repo_set_active.set_defaults(func='repo_set_active_cmd')
    parser_repo_set_active.add_argument('name', type=str, help='name of the repo')

    # "new" subcommand
    parser_new = subparsers.add_parser('new', help='create a new worktree')
    parser_new.set_defaults(func='new_cmd')
    parser_new.add_argument('name', type=str, help='name of the worktree')
    parser_new.add_argument('--repo', type=str, help='repo to use (overrides active repo)')

    # "rm" subcommand
    parser_rm = subparsers.add_parser('rm', help='removes a worktree')
    parser_rm.set_defaults(func='rm_cmd')
    parser_rm.add_argument('name', type=str, help='name of the worktree')
    parser_rm.add_argument('-f', '--force', action='store_true',
                            help='overrides the checks and forces the removal')
    parser_rm.add_argument('--repo', type=str, help='repo to use (overrides active repo)')

    # "ls" subcommand
    parser_ls = subparsers.add_parser('ls', help='lists available worktrees')
    parser_ls.set_defaults(func='ls_cmd')
    parser_ls.add_argument('--repo', type=str, help='repo to use (overrides active repo)')

    # "cd" subcommand
    parser_cd = subparsers.add_parser('cd', help='cd\'s to the specified worktree')
    parser_cd.set_defaults(func='cd_cmd')
    parser_cd.add_argument('name', type=str, help='name of the worktree')
    parser_cd.add_argument('--repo', type=str, help='repo to use (overrides active repo)')

    args = parser.parse_args()
    getattr(WorktreeWrapper(), args.func)(args)
