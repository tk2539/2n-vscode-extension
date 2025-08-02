
import * as vscode from 'vscode';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {
  let disposable = vscode.commands.registerCommand('2n-script-runner.runFile', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const doc = editor.document;
    const filePath = doc.fileName;

    const scriptPath = path.join(context.extensionPath, 'main.py');
    const terminal = vscode.window.createTerminal('2n Runner');
    terminal.show();
    terminal.sendText(`python3 "${scriptPath}" "${filePath}"`);
  });

  context.subscriptions.push(disposable);
}

export function deactivate() {}
