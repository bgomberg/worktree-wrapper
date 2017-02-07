# Worktree Wrapper (`ww`)
Wrapper around `git worktree` which makes it easier to create and manage worktrees, potentially involving multiple root repositories.

## Installation
Worktree-wrapper installs as a single `ww` command via the following steps:

1. Download / clone this repository
2. Add the `bin` folder to your `PATH`
3. Create an alias in your `.bashrc` (or equivalent) file: ```alias ww=". _ww.sh"```
4. (Optional) Source bin/ww_completions.bash to get auto-complete functionality.

## Command Documentation
The built-in help command `ww [...] -h` is the best and most up-to-date way to learn about the different `ww` commands and flags.

## Repository Setup
Once you install `ww`, you need to add a repository which you want to use it with. When you add a repo to `ww`, you assign it a name which will be used to identify it for future commands. The following steps provide a quick guide on adding a repo:

1. Clone the repo locally (somewhere out of the way since you shouldn't need to interact with it directly in the future)
2. Use `ww repo add ...` to add the repository and use `ww repo set-active ...` to set it as the active repository

## Example Workflow
Below is a basic example for what a development workflow looks like with `ww`.

### Pull Master
Since you generally don't ever touch the base repository (i.e. the one you originally cloned to) and it is always on the master branch, it's easy for master to get out of sync with origin. You can easily fix this using the `ww pull` command which will do a `git pull master` from your base repository.

### Create a New Worktree
The prefered workflow is to create a new worktree with every new branch you create. In other words, there's a 1:1 relationship between worktree and your active development branches. You do this using the `ww new ...` command. This creates a new branch based on master and creates a new worktree with this branch checked-out.

### Make Changes
You can now make changes to the contents of the worktree you created and use the branch within the worktree as you normally would (commit, push, etc).

### Merge Changes
If using arcanist, you can perform an equivalent to `arc land` by running `ww land` from outside of the worktree. This will also remove the worktree in the process.

## License and Contributions
The code contained within this repository is licensed under the GPLv3 license. See `LICENSE.md` for the complete text of the license. Pull requests and forks are welcome and encouraged if you find this program useful.
