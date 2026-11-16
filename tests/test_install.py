import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from rainbow import patch
class InstallTests(unittest.TestCase):
    def test_install_and_restore_preserve_personal_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            h=Path(directory); c=h/'.config'; (c/'omarchy').mkdir(parents=True)
            layout=c/'omarchy/shell.json'; layout.write_text('{"personal":"layout"}')
            prompt=c/'starship.toml'; prompt.write_text('# personal prompt\n')
            env=dict(os.environ,HOME=directory)
            result=subprocess.run(['bash',str(ROOT/'install.sh'),'--terminal','--no-apply'],env=env,capture_output=True,text=True,check=True)
            self.assertEqual(layout.read_text(),'{"personal":"layout"}')
            self.assertIn('80b8eb',prompt.read_text())
            conf=json.loads((c/'fastfetch/config.jsonc').read_text())
            self.assertIn('$HOME',conf['modules'][0]['text'])
            hook=c/'omarchy/hooks/theme-set.d/pastel-spectrum-sync'
            css=c/'gtk-3.0/gtk.css'; css.parent.mkdir(); css.write_text('/* personal */\n')
            for _ in range(2): subprocess.run(['bash',str(hook),'pastel-spectrum'],env=env,check=True)
            self.assertEqual(css.read_text().count('BEGIN PASTEL'),1)
            subprocess.run(['bash',str(hook),'other'],env=env,check=True)
            self.assertEqual(css.read_text(),'/* personal */\n')
            backup=result.stdout.split('Backup: ',1)[1].splitlines()[0]
            subprocess.run(['bash',str(ROOT/'install.sh'),'--restore',backup],env=env,check=True,capture_output=True)
            self.assertEqual(prompt.read_text(),'# personal prompt\n')
            self.assertFalse((c/'fastfetch/config.jsonc').exists())
            self.assertEqual(layout.read_text(),'{"personal":"layout"}')
    def test_rainbow_patch_is_idempotent_and_rejects_unknown_bars(self):
        source='import QtQuick\n  function publicLayoutConfig() {\n      id: componentLoader\n      id: registryLoader\n      id: qmlLoader\n'
        layout={'left':[{'id':'one'},{'id':'two'}]}
        result=patch(source,layout)
        self.assertEqual(patch(result,layout),result)
        self.assertEqual(result.count('layer.effect: MultiEffect'),3)
        with self.assertRaises(ValueError): patch('unknown format',layout)
if __name__=='__main__': unittest.main()
