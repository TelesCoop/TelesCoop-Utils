require(["base/js/namespace"], function(Jupyter){
    console.info('Binding Ctrl-J/K to move cell up/down');
    Jupyter.keyboard_manager.command_shortcuts.add_shortcut('Ctrl-k','jupyter-notebook:move-cell-up');
    Jupyter.keyboard_manager.command_shortcuts.add_shortcut('Ctrl-j','jupyter-notebook:move-cell-down');
});

// http://blog.rtwilson.com/how-to-get-sublime-text-style-editing-in-the-ipythonjupyter-notebook/
require(["codemirror/keymap/sublime", "notebook/js/cell", "base/js/namespace"],
    function(sublime_keymap, cell, IPython) {
    	console.info('codemirror sublime keymap');
        // setTimeout(function(){ // uncomment line to fake race-condition
        cell.Cell.options_default.cm_config.keyMap = 'sublime';
        var cells = IPython.notebook.get_cells();
        for(var cl=0; cl< cells.length ; cl++){
            cells[cl].code_mirror.setOption('keyMap', 'sublime');
        }
 
        // }, 1000)// uncomment  line to fake race condition 
    } 
);
