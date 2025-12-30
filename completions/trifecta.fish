# Fish shell completions for Trifecta CLI

# Disable file completion by default
complete -c trifecta -f

# --- Top Level Commands ---
complete -c trifecta -n "__fish_use_subcommand" -a create -d "Create a new Trifecta pack"
complete -c trifecta -n "__fish_use_subcommand" -a validate -d "Validate an existing Trifecta pack"
complete -c trifecta -n "__fish_use_subcommand" -a refresh-prime -d "Refresh the prime_*.md file"
complete -c trifecta -n "__fish_use_subcommand" -a load -d "Load relevant context for a task"
complete -c trifecta -n "__fish_use_subcommand" -a ctx -d "Manage Trifecta Context Packs"

# --- create ---
complete -c trifecta -n "__fish_seen_subcommand_from create" -l segment -s s -x -d "Segment name"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l path -s p -x -d "Target path"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l scope -x -d "Scope description"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l scan-docs -x -d "Docs dir to scan"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l profile -x -a "diagnose_micro impl_patch only_code plan handoff_log" -d "Default profile"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l dry-run -d "Preview without writing files"

# --- validate (Top Level) ---
complete -c trifecta -n "__fish_seen_subcommand_from validate; and not __fish_seen_subcommand_from ctx" -l path -s p -x -d "Path to Trifecta"

# --- refresh-prime ---
complete -c trifecta -n "__fish_seen_subcommand_from refresh-prime" -l path -s p -x -d "Path to Trifecta"
complete -c trifecta -n "__fish_seen_subcommand_from refresh-prime" -l scan-docs -x -d "Docs dir to scan"

# --- load ---
complete -c trifecta -n "__fish_seen_subcommand_from load" -l segment -s s -x -d "Segment name or path"
complete -c trifecta -n "__fish_seen_subcommand_from load" -l path -s p -x -d "Segment name or path"
complete -c trifecta -n "__fish_seen_subcommand_from load" -l task -s t -x -d "Task description"
complete -c trifecta -n "__fish_seen_subcommand_from load" -l mode -s m -x -a "pcc fullfiles" -d "Loading mode"

# --- ctx group ---
set -l ctx_commands build search sync get validate
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and not __fish_seen_subcommand_from $ctx_commands" -a build -d "Build context pack"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and not __fish_seen_subcommand_from $ctx_commands" -a search -d "Search context pack"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and not __fish_seen_subcommand_from $ctx_commands" -a sync -d "Run Autopilot sync"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and not __fish_seen_subcommand_from $ctx_commands" -a get -d "Retrieve chunks"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and not __fish_seen_subcommand_from $ctx_commands" -a validate -d "Validate context pack"

# --- ctx build ---
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from build" -l segment -s s -x -d "Segment name or path"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from build" -l path -s p -x -d "Segment name or path"

# --- ctx search ---
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from search" -l segment -s s -x -d "Segment name or path"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from search" -l path -s p -x -d "Segment name or path"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from search" -l query -s q -x -d "Search query"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from search" -l limit -s k -x -d "Max results"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from search" -l doc -x -a "skill agent session prime" -d "Filter by doc type"

# --- ctx sync ---
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from sync" -l segment -s s -x -d "Segment name or path"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from sync" -l path -s p -x -d "Segment name or path"

# --- ctx get ---
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from get" -l segment -s s -x -d "Segment name or path"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from get" -l path -s p -x -d "Segment name or path"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from get" -l ids -x -d "Comma-separated chunk IDs"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from get" -l mode -s m -x -a "raw excerpt skeleton" -d "Retrieval mode"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from get" -l budget -l budget-token-est -x -d "Token budget"

# --- ctx validate ---
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from validate" -l segment -s s -x -d "Segment name or path"
complete -c trifecta -n "__fish_seen_subcommand_from ctx; and __fish_seen_subcommand_from validate" -l path -s p -x -d "Segment name or path"

# Help
complete -c trifecta -l help -s h -f -d "Show help"
