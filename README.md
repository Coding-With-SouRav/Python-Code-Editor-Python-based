# VSCode-Like Python Editor: Feature Overview

Core Features
Code Editing

Syntax Highlighting: Custom colors for Python keywords, data types, strings, comments, brackets, and imports.

Line Numbers: Dynamic numbering with current line highlighting.

Auto-Indentation: Smart indentation on Enter and code block detection (e.g., : for loops/functions).

Bracket/Quote Auto-Completion: Automatically closes (), {}, [], '', "".

Multiple Cursors: Partial support via keyboard shortcuts.

File & Project Management

File Explorer: Tree view for folders/files with icons for file types (Python, HTML, CSS, images, etc.).

Tabs: Multi-file editing with tab switching, closing, and scrollable tab bar.

File Operations: Create/delete files/folders, rename, cut/copy/paste, drag-and-drop support.

Auto-Save: Periodic saving of opened files.

Terminal Integration

In-built Terminal: Run Python scripts, execute shell commands, input handling, and process management (stop/kill).

Output Highlighting: Errors, warnings, and AI responses are color-coded.

Advanced Features
Code Intelligence

Autocompletion: Jedi library-powered suggestions with fuzzy matching.

Go-to-Definition: Ctrl + Click to jump to function/class definitions.

Error Checking: Real-time syntax validation using ast module.

Search & Replace

Find/Replace Dialog: Regex-free search, match highlighting, and replace history (undo/redo).

Cross-File Search: F3 to search text across files in the opened folder.

AI Integration

Google Generative AI: Code suggestions and queries via Ask to AI... search bar.

Theming & Customization

Dark Themes: Black, Dark Blue, Dark Green, Dark Gray.

Font Sizing: Zoom in/out with Ctrl++/Ctrl+-.

Productivity Tools
Undo/Redo: For both code edits and file operations (e.g., file deletion).

Code Manipulation:

Duplicate Lines (Alt+Shift+Down).

Move Lines (Alt+Up/Down).

Toggle Comments (Ctrl+/).

Keyboard Shortcuts: Over 50+ shortcuts (e.g., Alt+S to run, Ctrl+Q to stop).

UI/UX Highlights
Custom Widgets:

Floating search/replace dialog with live match counts.

Tooltips and reverse tooltips for buttons.

Context menus for files/folders.

Responsive Layout: Resizable panes for editor, terminal, and file explorer.

Visual Feedback:

Highlighting for replaced text, syntax errors, and search matches.

Animated line highlights and selection borders.

Under-the-Hood
File Monitoring: watchdog integration to auto-refresh the file tree on external changes.

Cross-Platform: Supports Windows/macOS/Linux (uses TkinterDnD for drag-and-drop).

Resource Management: Icons and assets bundled for PyInstaller compatibility.

Potential Extensions
Plugin system for language support (e.g., JavaScript, C++).

Git integration for version control.

Customizable keybindings via JSON/INI.

This editor combines core code-editing tools with advanced features like AI assistance and terminal integration, aiming to replicate a lightweight VSCode experience optimized for Python development.

# Demo UI (Image)


![Screenshot 2025-04-19 204608](https://github.com/user-attachments/assets/aabfff9d-9adb-4c8a-944a-5200f259b4d9)

![Screenshot 2025-04-19 204506](https://github.com/user-attachments/assets/935d82ad-52a7-40e9-a078-1c5877bacf36)

![Screenshot 2025-04-19 204433](https://github.com/user-attachments/assets/e39fad1c-fb30-44b9-af3e-21bdae1bf1d4)

![Screenshot 2025-04-19 204403](https://github.com/user-attachments/assets/979fcf06-4845-4930-ae45-b1bf9e49bb5e)

![Screenshot 2025-04-19 205201](https://github.com/user-attachments/assets/4c41b625-1e17-4662-a469-df85141f86aa)

![Screenshot 2025-04-19 204916](https://github.com/user-attachments/assets/e046b573-1e2d-4fa1-a35b-f438086e220c)

![Screenshot 2025-04-19 204842](https://github.com/user-attachments/assets/35be98f4-1788-485f-947d-3a237a3785c1)

![Screenshot 2025-04-19 204738](https://github.com/user-attachments/assets/8ccab2cc-528d-437b-a5fb-020b379be25e)

![Screenshot 2025-04-19 204631](https://github.com/user-attachments/assets/2b572f0c-aef4-44eb-acf1-b3ddc6130a48)
