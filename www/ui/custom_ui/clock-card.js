const LitElement = Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
const html = LitElement.prototype.html;

class ClockCard extends LitElement {

  render() {
    return html`
          <style>
        :host {
          cursor: pointer;
        }
        .content {
          padding: 24px 16px;
          display:flex;
        }
        .gtlogo{
	        background-image: url("/local/ui/logo.png");
		    background-size: contain;
		    background-repeat: no-repeat;
		    width:92px;
        }
        .time {
          font-family: var(--paper-font-headline_-_font-family);
          -webkit-font-smoothing: var(--paper-font-headline_-_-webkit-font-smoothing);
          font-size: 3em;
          font-weight: var(--paper-font-headline_-_font-weight);
          letter-spacing: var(--paper-font-headline_-_letter-spacing);
          line-height: 1em;
          text-rendering: var(--paper-font-common-expensive-kerning_-_text-rendering);
        }
        .date {
	      color: var(--primary-color);
          font-family: var(--paper-font-headline_-_font-family);
          -webkit-font-smoothing: var(--paper-font-headline_-_-webkit-font-smoothing);
          font-size: 1.3em;
          font-weight: var(--paper-font-headline_-_font-weight);
          letter-spacing: var(--paper-font-headline_-_letter-spacing);
          line-height: var(--paper-font-headline_-_line-height);
          text-rendering: var(--paper-font-common-expensive-kerning_-_text-rendering);
        }
      </style>
      <ha-card>
        <div class="content">
	      <div class="gtlogo"></div>
	      <div class="clock">
		    <div class="time" id="time">--:--</div>
		    <div class="date" id="date"></div>
	      </div>
        </div>
      </ha-card>
     `
  }
  
  static get properties() {
    return {
      hass: Object,
      config: Object,
    };
  }

  firstUpdated() {
    this.time = this.shadowRoot.getElementById('time');
    this.date = this.shadowRoot.getElementById('date');

    this._updateTime();
    setInterval(() => this._updateTime(), 1000);
  }
  
  setConfig(config) {
    this.config = config;
  }

  _updateTime(force = false) {
    if (window.moment) {
      moment.locale(this.hass.language);
      this.time.innerHTML = moment().format('LT');
      this.date.innerHTML = moment().format('dddd, LL');
    }
  }

  // The height of your card. Home Assistant uses this to automatically
  // distribute all cards over the available columns.
  getCardSize() {
    return 3;
  }
}

customElements.define('clock-card', ClockCard);
