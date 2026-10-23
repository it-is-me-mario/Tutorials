# Maintaining tutorials

- Explain the purpose, environment, input files and output location in Markdown cells. Keep the code focused on the calculation.
- For external data, document the access URL, any account requirement, the release directory and the files actually read. Distinguish release dates from reference years.
- Replace personal filesystem paths with explicit placeholders. Do not commit local datasets, credentials or machine-specific notebook metadata.
- When adapting an existing notebook without changing its code, compare its code cells with the source. Allow only the agreed path substitutions; put explanations in Markdown cells.
- Clear saved outputs and execution counts when preparing an unexecuted, portable copy. Validate notebook structure and code syntax, and state whether the full calculation was rerun.
- Before committing, inspect repository status and include only the intended tutorial files. Preserve unrelated local changes.
