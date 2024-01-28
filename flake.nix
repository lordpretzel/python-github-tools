{
  description = "bib cleaner";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-23.05";
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

          # Utility to run a script easily in the flakes app
          simple_script = name: add_deps: text: let
            exec = pkgs.writeShellApplication {
              inherit name text;
              runtimeInputs = with pkgs; [
                (mach-nix.lib."${system}".mkPython {
                  requirements = builtins.readFile requirements-txt;
                })
              ] ++ add_deps;
            };
          in {
            type = "app";
            program = "${exec}/bin/${name}";
          };

        in with pkgs;
          {
            ###################################################################
            #                       running                                   #
            ###################################################################
            apps = {
              default = simple_script "clean_bib" [] ''
                echo "args are: " "''$@"
                python github-tools.py "''$@"
              '';
            };

            ###################################################################
            #                       development shell                         #
            ###################################################################
            devShells.default = mach-nix.lib."${system}".mkPythonShell # mkShell
              {
                # requirementx
                requirements = builtins.readFile requirements-txt;
                # python version
                # nativeBuildInputs = with pkgs; [
                #   python38
                #   python38Packages.pip
                #   poetry
                # ];
              };
          }
      );
}
