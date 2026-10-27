    # SigmaOS-common

    Shared helpers + policy kit used by every applet

    Part of the **SigmaOS** sovereign operating-system ecosystem — a multi-repository
    distribution modelled on Linux Mint and Omarchy Linux. See the parent
    [`SigmaOS`](https://github.com/AaryanSinghChauhan09/SigmaOS) repository for the
    full component index.

    ## Upstream inspirations
    - https://github.com/linuxmint/mintcommon

    ## Design principles applied
    - **DRY**
- **Information Hiding**
- **Defensive Programming**
- **Fail-Fast**
- **KISS**
- **Deterministic Testing**

    ## Usage
    Verbs: `config-get, config-set, xrandr-plan, paths`

    ```
    $ sigma-common config-get --file app.conf --key ui.theme
$ sigma-common config-set --file app.conf --key ui.theme --value dark --type str
$ sigma-common config-set --file app.conf --key ui.scale --value 1.25 --type float
$ sigma-common xrandr-plan --output eDP-1 --mode 1920x1080 --pos 0x0 --primary
$ sigma-common paths

    ```

    ## Build & test
    ```
    make build
    make test
    ```

    ## Licence
    GNU General Public License v3.0 (FOSS).
