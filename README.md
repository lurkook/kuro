<p align="center">
  <img src="https://static.wikia.nocookie.net/dokodemo/images/6/61/KuroSmug.png"
       alt="Kuro (Doko Demo Issyo series)">
</p>

<h1 align="center">Kuro</h1>

UbiArt texture encoder for Wii games.

### Features
- Masked texture support
- Command line interface
- Batch convert support
- Minimal dependencies to external programs *(program is needs only Wiimms Image Tool for encoding textures)*
- Powered by PIL library *(this helps to make real alpha images for masked textures)*

### Usage
```
kuro.py -i INPUT [-o OUTPUT] [-w WIMGT_EXECUTABLE_PATH] [-m] [-e EXTENSION_NAME]

optional arguments:
  -i INPUT, --input INPUT
                        Input image(s)
  -o OUTPUT, --output OUTPUT
                        Output directory
  -w WIMGT_EXECUTABLE_PATH, --wimgt-executable-path WIMGT_EXECUTABLE_PATH
                        Path to Wiimms Image Tool
  -m, --masked          Texture should be masked?
  -e EXTENSION_NAME, --extension-name EXTENSION_NAME
                        Name of extension what should be used for output file names (example. tga/png)
```

### Contribute!
Any contribution, bug reports and help is welcome here.

Check [issue page](https://github.com/lurkook/kuro/issues).

### License
This repository ([lurkook/kuro](https://github.com/lurkook/kuro)) is licensed under [Apache License 2.0](https://github.com/lurkook/kuro/blob/master/LICENSE).
