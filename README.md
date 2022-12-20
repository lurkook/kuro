<p align="center">
  <img src="https://static.wikia.nocookie.net/dokodemo/images/6/61/KuroSmug.png"
       alt="Kuro (Doko Demo Issyo series)">
</p>

<h1 align="center">Kuro</h1>

UbiArt texture encoder for Wii games.

### Features
- Masked texture support
- Command line interface
- Minimal dependencies to external programs *(program is needs only Wiimm Image Tool for encoding textures)*
- Powered by PIL library *(this helps to make real alpha images for masked textures)*

### TODO
- [ ] Batch convert support
- [ ] Move to custom CMPR encoding from Wiimm Image Tool
- [ ] Test output textures in Rayman games

### Command-line parameters
```
-i INPUT, --input INPUT
                        Input image
-o OUTPUT, --output OUTPUT
                        Output texture
-w WIMGT_EXECUTABLE_PATH, --wimgt-executable-path WIMGT_EXECUTABLE_PATH
                        Path to Wiimms Image Tool
-m, --masked            Texture should be masked?
```

### Contribute!
Any contribution, bug reports and help is welcome here.

Check [issue page](https://github.com/lurkook/kuro/issues).

### License
This repository ([lurkook/kuro](https://github.com/lurkook/kuro)) is licensed under [Apache License 2.0](https://github.com/lurkook/kuro/blob/master/LICENSE).
