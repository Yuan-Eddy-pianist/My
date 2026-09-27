# Relocation verification — 27 September 2026

Current home: `/Users/eddy/Desktop/My/agent-workflow`.

- The Firstmate checkout, local projects, private task records, and available primary/worker conversation files were moved into the kit. The old Firstmate project directory no longer exists.
- Existing files and changes in the surrounding My application were preserved.
- Firstmate tracked source remains clean. The relocated workflow-demo passed all five Node tests.
- Portable command files passed shell syntax checks; the three Python helpers passed parsing checks.
- Device configuration ran successfully, and the legacy Firstmate launcher redirects to the new location.
- The transfer helper completed successfully without deleting working copies. It stopped the named Firstmate session, preserved runtime records, and captured portable settings.
- Restart was tested twice and produced one primary Pi agent, idle and ready in the new project directory. The terminal launcher started a WezTerm process with an attached Herdr client. Visual inspection was unavailable.
- The private Firstmate checkout, sessions, archives, and local runtime are ignored by the surrounding My Git repository. Copy the whole folder with hidden files; cloning My alone is not a complete transfer.
- Credentials were not exported. Installed applications remain on the host; Setup.command is the reinstall/configuration recipe.

The original history is retained. Moving to a different path may begin a fresh primary conversation; historical session files are not rewritten. A restore on a second Mac, Linux, or WSL has not been executed because no destination device has been selected.
