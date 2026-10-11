# HISTORY.md split into one file per entry

On 2026-10-12 HISTORY.md (2,512 bytes, 1 entry; `git show 4afe220:HISTORY.md` is the file as it was) was split into the files of history/, one per entry, by ~/cloud/code/dotfiles/bin/history-split, and deleted. Every entry used to be inserted at the top of that one file, so two sessions in one working tree committed each other's half-written entries, and two clones always conflicted at that place; a file per entry is staged alone. The rule is in the global instructions, "AGENTS.md is the present, history/ the past".

- **Names.** It carries the minute of the commit that brought it (`git blame`), a little after it was written.
- **Text.** Each file is `# title`, then the entry as it stood. The script read the bodies back from the new files, put them between the old heading lines and the blank lines that separated them, and got the old file byte for byte (sha256 e6029c2ae75da46bf47bd689d2d57e444a9fa0ed296fa2876ac526d926ee38f8).
- **Not carried over:** the heading lines (their dates are in the names, their titles in the first lines), and the lines the file opened with:

      # History

      What was done in this repo and when, newest first: changes to the instructions and docs, results of past runs, states that no longer hold. AGENTS.md and docs/ say what is true now. This file is not loaded at the start of a session; read it to find out how something got the way it is.
