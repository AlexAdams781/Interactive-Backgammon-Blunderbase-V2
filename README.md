# Interactive-Backgammon-Blunderbase-V2
The second version of this project.

Updates:
- Added exit and restart buttons for each instance of the program
- Allowed user to move checkers or make cubing decisions and keeps counter of correct/mistake/blunder moves
- Caches analysis on a separate directory, significantly improving speed
- Implements worker thread that runs analysis in the background

To do list for V3:
- Migrate entirely out of the CLI into UI
  - Add position button
    - Add position to the database
    - Add to all decks that the filter allows
  - Create deck button
    - Adds a filter and creates a deck
  - Play deck button
  - Ply analysis button
    - Changes the ply for all future analysis
    - Add ply text to each card
- Fix move identification (bug)
- Add star option and add another deck with starred positions only
