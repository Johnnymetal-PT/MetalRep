import {
    Component,
    useState,
    useSubEnv,
} from "@odoo/owl";
import { OptionsContainer } from "@html_builder/sidebar/option_container";
import { useOptionsSubEnv } from "@html_builder/utils/utils";

export class ThemeTabExt extends Component {
    static template = "theme_clarico_vega.ThemeTabExt";
    static components = { OptionsContainer };
    static props = {
        optionsContainers: { type: Array, optional: true },
        colorPresetToShow: { type: Number | null, optional: true },
    };
    static defaultProps = {
        optionsContainers: [],
    };

    setup() {
        useOptionsSubEnv(() => [this.env.editor.document.body]);
        useSubEnv({
            colorPresetToShow: this.props.colorPresetToShow,
        });
        this.state = useState({
            fontsData: {},
        });
        this.optionsContainersExt =
            this.props.optionsContainers?.length
                ? this.props.optionsContainers
                : (this.env.editor.resources["themeext_options"] || []);
    }
}
