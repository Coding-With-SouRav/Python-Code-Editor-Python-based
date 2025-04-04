VSCode-Like Python Editor: Feature Overview

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
