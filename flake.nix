{
  description = "tools for github API scripting";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
    mach-nix.url = "github:DavHau/mach-nix";
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix, ... }@inputs:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = import nixpkgs {
            inherit system;
          };

          requirements-txt = "${self}/requirements.txt";
          requirements-as-text = builtins.readFile requirements-txt;

          python="python311";

          # python environment
          mypython =
            mach-nix.lib."${system}".mkPython {
              inherit python;
              requirements = requirements-as-text;
            };

          mydevpython =
            mach-nix.lib."${system}".mkPython {
              inherit python;
              requirements = requirements-as-text +  ''
pip
python-lsp-server[all]
mypy
'';
            };

          # Utility to run a script easily in the flakes app
          simple_script = name: add_deps: text: let
            exec = pkgs.writeShellApplication {
              inherit name text;
              runtimeInputs = with pkgs; [
                mypython
              ] ++ add_deps;
            };
          in {
            type = "app";
            program = "${exec}/bin/${name}";
          };

          script-base-name = "github-tools";
          script-name = "${script-base-name}.py";
          pyscript = "${self}/${script-name}";
          package-version = "1.0";
          package-name = "${script-base-name}-${package-version}";

        in with pkgs;
          {
            ###################################################################
            #                       package                                   #
            ###################################################################
            packages = {
              github-tools = stdenv.mkDerivation {
                name="${package-name}";
                src = ./.;

                runtimeInputs = [ mypython ];
                buildInputs = [ mypython ];
                nativeBuildInputs = [ makeWrapper ];
                installPhase = ''
                  mkdir -p $out/bin/
                  mkdir -p $out/share/
                  cp ${pyscript} $out/share/${script-name}
                  makeWrapper ${mypython}/bin/python $out/bin/${script-base-name} --add-flags "$out/share/${script-name}"
                '';
              };
            };

            ###################################################################
            #                       running                                   #
            ###################################################################
            apps = {
              default = simple_script "pyscript" [] ''
                python ${pyscript} "''$@"
              '';
            };

            ###################################################################
            #                       development shell                         #
            ###################################################################
            devShells.default = mkShell
              {
                buildInputs = [
                  mydevpython
                  rich-cli
                ];
                runtimeInputs = [
                  mydevpython
                  rich-cli
                ];
                shellHook = ''
                  alias pip="${mydevpython}/bin/pip --disable-pip-version-check"
                  rich "[b white on black]Using virtual environment for [/][b white on red] ${package-name} [/][b white on black] with Python[/]

[b]$(python --version)[/]

[b white on black]with packages[/]

$(${mydevpython}/bin/pip list --no-color --disable-pip-version-check)" --print --padding 1 -p -a heavy
                '';
              };
          }
      );
}
