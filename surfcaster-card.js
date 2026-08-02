import { LitElement, html, css } from "https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js";

class SurfcasterCard extends LitElement {
	static get properties() {
		return {
			hass: { type: Object },
			config: { type: Object },
		};
	}

	static get styles() {
		return css`
			:host {
				display: block;
			}
			ha-card {
				padding: 16px;
			}
			.spot-name {
				font-size: 1.1em;
				font-weight: 600;
				margin-bottom: 12px;
				display: flex;
				align-items: center;
				gap: 6px;
			}
			.metrics {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
				gap: 10px;
			}
			.metric {
				text-align: center;
				padding: 8px 4px;
				border-radius: 8px;
				background: var(--card-background-color, #1c1c1c);
			}
			.metric ha-icon {
				display: block;
				margin: 0 auto 2px;
				--mdc-icon-size: 20px;
			}
			.metric .value {
				font-size: 1.3em;
				font-weight: 700;
			}
			.metric .label {
				font-size: 0.65em;
				opacity: 0.7;
				text-transform: uppercase;
				letter-spacing: 0.5px;
			}
			.metric.wave {
				border-left: 3px solid var(--surf-wave, #4285f4);
			}
			.metric.period {
				border-left: 3px solid var(--surf-period, #0f9d58);
			}
			.metric.wind {
				border-left: 3px solid var(--surf-wind, #f4b400);
			}
			.metric.max {
				border-left: 3px solid var(--surf-max, #9c27b0);
			}
		`;
	}

	setConfig(config) {
		this.config = config;
		this._spot = config.spot;
	}

	_renderMetric(hass, entityId, label, icon, cssClass) {
		const state = entityId ? hass.states[entityId] : null;
		const value = state ? state.state : "—";
		const unit = state ? state.attributes.unit_of_measurement || "" : "";
		return html`
			<div class="metric ${cssClass}">
				<ha-icon icon="${icon}"></ha-icon>
				<div class="value">${value}<span style="font-size:0.55em">${unit}</span></div>
				<div class="label">${label}</div>
			</div>
		`;
	}

	render() {
		if (!this.hass || !this.config) return html``;
		const spot = this._spot;
		const prefix = `sensor.${spot}_`;

		const spotEntity = this.hass.states[`${prefix}wave_height`];
		const spotName = spotEntity
			? spotEntity.attributes.friendly_name.replace(" Wave Height", "")
			: spot;

		return html`
			<ha-card>
				<div class="spot-name">
					<ha-icon icon="mdi:waves"></ha-icon>
					${spotName}
				</div>
				<div class="metrics">
					${this._renderMetric(this.hass, `${prefix}wave_height`, "Wave", "mdi:waves", "wave")}
					${this._renderMetric(this.hass, `${prefix}wave_period`, "Period", "mdi:timeline-clock", "period")}
					${this._renderMetric(this.hass, `${prefix}wind_speed`, "Wind", "mdi:weather-windy", "wind")}
					${this._renderMetric(this.hass, `${prefix}wave_height_max`, "Max", "mdi:waves-arrow-up", "max")}
				</div>
			</ha-card>
		`;
	}

	static getStubConfig() {
		return { spot: "spo" };
	}
}

customElements.define("surfcaster-card", SurfcasterCard);

window.customCards = window.customCards || [];
window.customCards.push({
	type: "surfcaster-card",
	name: "Surfcaster Card",
	description: "Surf conditions at a glance — wave height, period, wind.",
});
