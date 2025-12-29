# Fish shell completions for Trifecta CLI

# Complete commands
complete -c trifecta -f

# create command
complete -c trifecta -n "__fish_use_subcommand" -a create -d "Create a new Trifecta pack"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l segment -s s -x -d "Segment name"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l path -s p -x -d "Target path"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l scope -x -d "Scope description"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l scan-docs -x -d "Docs dir to scan"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l profile -x -a "diagnose_micro impl_patch only_code plan handoff_log" -d "Default profile"
complete -c trifecta -n "__fish_seen_subcommand_from create" -l dry-run -d "Preview without writing files"

# validate command
complete -c trifecta -n "__fish_use_subcommand" -a validate -d "Validate an existing Trifecta pack"
complete -c trifecta -n "__fish_seen_subcommand_from validate" -l path -s p -x -d "Path to Trifecta"

# refresh-prime command
complete -c trifecta -n "__fish_use_subcommand" -a refresh-prime -d "Refresh the prime_*.md file"
complete -c trifecta -n "__fish_seen_subcommand_from refresh-prime" -l path -s p -x -d "Path to Trifecta"
complete -c trifecta -n "__fish_seen_subcommand_from refresh-prime" -l scan-docs -x -d "Docs dir to scan"

# help option
complete -c trifecta -l help -s h -f -d "Show help and exit"
