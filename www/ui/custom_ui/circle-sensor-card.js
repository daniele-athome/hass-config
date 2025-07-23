const LitElement = Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class CircleSensorCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      state: { type: Object },
      dashArray: { type: String },
      _hass: { type: Object }
    }
  }

  render() {
    const content = html`
      <div class="container" @click="${this._click}">
        <svg viewbox="0 0 200 200" id="svg">
          <!-- Definitionen für Filter und Gradienten -->
          <defs>
            <!-- Weicher Schatten für den Fortschrittskreis -->
            <filter id="circle-shadow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
              <feOffset dx="1" dy="1" result="offsetblur"/>
              <feFlood flood-color="rgba(0,0,0,0.3)"/>
              <feComposite in2="offsetblur" operator="in"/>
              <feMerge>
                <feMergeNode/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            
            <!-- Radialer Gradient für den Fortschrittskreis -->
            <linearGradient id="circle-gradient" gradientTransform="rotate(90)">
              <stop offset="0%" stop-color="var(--gradient-color-1, ${this.config.stroke_color || '#03a9f4'})"/>
              <stop offset="100%" stop-color="var(--gradient-color-2, ${this.config.stroke_color || '#03a9f4'})"/>
            </linearGradient>
          </defs>

          <circle id="circlestrokebg" 
            cx="50%" 
            cy="50%" 
            r="45%"
            fill="${this.config.fill || 'rgba(255, 255, 255, .75)'}"
            stroke="${this.config.stroke_bg_color || '#999999'}"
            stroke-width="${this.config.stroke_bg_width}"
            stroke-linecap="${this.config.stroke_linecap || 'butt'}"
            transform="rotate(-90 100 100)"/>
          <circle id="circle" 
            cx="50%" 
            cy="50%" 
            r="45%"
            fill="${this.config.fill || 'rgba(255, 255, 255, .75)'}"
            stroke="${this.config.use_gradient ? 'url(#circle-gradient)' : (this.config.stroke_color || '#03a9f4')}"
            stroke-dasharray="${this.dashArray}"
            stroke-width="${this.config.stroke_width || 6}"
            stroke-linecap="${this.config.stroke_linecap || 'butt'}"
            filter="${this.config.use_shadow ? 'url(#circle-shadow)' : 'none'}"
            transform="rotate(-90 100 100)"/>
        </svg>
        <span class="labelContainer">
          ${this._renderContent()}
        </span>
      </div>
    `;

    return this.config?.show_card === false ? content : html`<ha-card>${content}</ha-card>`;
  }

  static get styles() {
    return css`
      :host {
        display: inline-block;
        cursor: pointer;
        position: relative;
        width: var(--circle-sensor-width, 100%);
        height: var(--circle-sensor-height, 100%);
        background: var(--card-background-color, white);
        border-radius: var(--ha-card-border-radius, 4px);
        box-shadow: var(--ha-card-box-shadow, 0 2px 2px 0 rgba(0,0,0,.14), 0 3px 1px -2px rgba(0,0,0,.2), 0 1px 5px 0 rgba(0,0,0,.12));
      }

      :host([no-card]) {
        background: transparent;
        border-radius: 0;
        box-shadow: none;
      }

      .container {
        position: relative;
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
      }

      svg {
        width: 100%;
        height: 100%;
      }

      .labelContainer {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 4px;
      }
      
      #label {
        display: flex;
        line-height: 1;
        align-items: center;
      }
      
      #label.bold {
        font-weight: bold;
      }
      
      #label, #name {
        margin: 1% 0;
      }

      .text, #name {
        font-size: 100%;
      }
      
      .unit {
        font-size: 75%;
      }
      
      .icon {
        margin: 4px;
        color: var(--primary-text-color);
        --mdc-icon-size: 20px;
      }
      
      /* Neue Animation definieren */
      @keyframes rotate {
        from {
          transform: rotate(0deg);
        }
        to {
          transform: rotate(360deg);
        }
      }
      
      /* Klasse für rotierende Icons */
      .icon.rotating {
        animation: rotate var(--rotation-duration, 2s)     /* Dauer */
                  var(--rotation-timing, linear)           /* Timing-Funktion */
                  var(--rotation-delay, 0s)               /* Verzögerung */
                  var(--rotation-iteration, infinite)     /* Wiederholungen */
                  var(--rotation-direction, normal);      /* Richtung */
      }
      
      .icon:hover {
        transform: scale(1.1);
      }
      
      .text {
        font-size: var(--value-font-size, 100%);
      }
      
      .unit {
        font-size: var(--unit-font-size, 75%);
      }
    `;
  }

  firstUpdated() {
    if (this.config) {
      this._updateConfig();
    }
  }

  setConfig(config) {
    if (!config.entity) {
      throw Error('No entity defined')
    }
    
    this.config = config;
    
    if (this.hasUpdated) {
      this._applyConfig();
    }
  }

  _applyConfig() {
    if (this.state && this._hass) {
      const state = this.config.attribute
        ? this.state.attributes[this.config.attribute]
        : this.state.state;
      
      let colorStops = {};
      if (this.config.color_stops) {
        Object.entries(this.config.color_stops).forEach(([key, value]) => {
          colorStops[key] = value;
        });
      }
      if (Object.keys(colorStops).length === 0) {
        colorStops[this.config.min || 0] = this.config.stroke_color || '#03a9f4';
      }

      this._updateCircleColor(state, colorStops, this._hass);
    }
    
    this._updateConfig();
  }

  getCardSize() {
    return 3;
  }

  _updateConfig() {
    const container = this.shadowRoot?.querySelector('.labelContainer');
    if (!container) return;

    container.style.color = 'var(--primary-text-color)';

    if (this.config.font_style) {
      Object.keys(this.config.font_style).forEach((prop) => {
        if (prop === 'value_size') {
          this.style.setProperty('--value-font-size', this.config.font_style.value_size);
        } else if (prop === 'unit_size') {
          this.style.setProperty('--unit-font-size', this.config.font_style.unit_size);
        } else {
          container.style.setProperty(prop, this.config.font_style[prop]);
        }
      });
    }

    if (this.config.style) {
      Object.entries(this.config.style).forEach(([prop, value]) => {
        this.style.setProperty(prop, value);
      });
    }
  }

  set hass(hass) {
    this._hass = hass;
    const oldState = this.state;
    this.state = hass.states[this.config.entity];

    if (oldState === this.state) {
      return;
    }

    if (this.config.attribute) {
      if (!this.state.attributes[this.config.attribute] ||
          isNaN(this.state.attributes[this.config.attribute])) {
        console.error(`Attribute [${this.config.attribute}] is not a number`);
        return;
      }
    } else {
      if (!this.state || isNaN(this.state.state)) {
        console.error(`State is not a number`);
        return;
      }
    }

    const state = this.config.attribute
      ? this.state.attributes[this.config.attribute]
      : this.state.state;
    const r = 200 * .45;
    const min = this._getValue(this.config.min, hass);
    const max = this._getValue(this.config.max, hass);
    const val = this._calculateValueBetween(min, max, state);
    const score = val * 2 * Math.PI * r;
    const total = 10 * r;
    this.dashArray = `${score} ${total}`;

    let colorStops = {};
    if (this.config.color_stops) {
      Object.entries(this.config.color_stops).forEach(([key, value]) => {
        colorStops[key] = value;
      });
    }
    if (Object.keys(colorStops).length === 0) {
      colorStops[min] = this.config.stroke_color || '#03a9f4';
    }

    this._updateCircleColor(state, colorStops, hass);
  }

  _click() {
    this._fire('hass-more-info', { entityId: this.config.entity });
  }

  _calculateStrokeColor(state, stops, isIcon = false, hass) {
    const convertedStops = {};
    const lessThanStops = {};
    
    // Zuerst alle Stops in die entsprechenden Objekte konvertieren
    Object.entries(stops).forEach(([key, value]) => {
      if (key.startsWith('<')) {
        const numValue = key.substring(1);
        if (numValue === 'min' && this.config.min) {
          const minValue = this._getBaseSensorValue(this.config.min, hass);
          lessThanStops[minValue] = value;
        } else if (numValue === 'max' && this.config.max) {
          const maxValue = this._getBaseSensorValue(this.config.max, hass);
          lessThanStops[maxValue] = value;
        } else if (numValue.includes('min+') || numValue.includes('min-') || 
                   numValue.includes('max+') || numValue.includes('max-')) {
          const parts = numValue.match(/(min|max)([\+\-])([\d.]+)/);
          if (parts) {
            const [, base, operator, number] = parts;
            const baseValue = this._getBaseSensorValue(this.config[base], hass);
            const offset = parseFloat(number);
            const calculatedKey = operator === '+' 
              ? baseValue + offset 
              : baseValue - offset;
            lessThanStops[calculatedKey] = value;
          }
        } else {
          lessThanStops[parseFloat(numValue)] = value;
        }
      } else {
        if (key === 'min' && this.config.min) {
          const minValue = this._getBaseSensorValue(this.config.min, hass);
          convertedStops[minValue] = value;
        } else if (key === 'max' && this.config.max) {
          const maxValue = this._getBaseSensorValue(this.config.max, hass);
          convertedStops[maxValue] = value;
        } else if (key.includes('min+') || key.includes('min-') || 
                   key.includes('max+') || key.includes('max-')) {
          const parts = key.match(/(min|max)([\+\-])([\d.]+)/);
          if (parts) {
            const [, base, operator, number] = parts;
            const baseValue = this._getBaseSensorValue(this.config[base], hass);
            const offset = parseFloat(number);
            const calculatedKey = operator === '+' 
              ? baseValue + offset 
              : baseValue - offset;
            convertedStops[calculatedKey] = value;
          }
        } else {
          convertedStops[parseFloat(key)] = value;
        }
      }
    });
    
    // Wenn kein Gradient, prüfe die Stops in der richtigen Reihenfolge
    if ((isIcon && !this.config.icon_gradient) || (!isIcon && !this.config.gradient)) {
      // Zuerst die normalen Stops prüfen (von hoch nach niedrig)
      const normalValues = Object.keys(convertedStops).map(Number).sort((a, b) => b - a);
      for (const stop of normalValues) {
        if (state >= stop) {
          return convertedStops[stop];
        }
      }
      
      // Dann die "kleiner als" Stops prüfen (von niedrig nach hoch)
      const lessThanValues = Object.keys(lessThanStops).map(Number).sort((a, b) => a - b);
      for (const stop of lessThanValues) {
        if (state < stop) {
          return lessThanStops[stop];
        }
      }
      
      // Fallback auf die Standard-Farbe
      return this.config.stroke_color || '#03a9f4';
    }
    
    // Mit Gradient - Interpolation zwischen den normalen Stops
    const sortedStops = Object.keys(convertedStops).map(Number).sort((a, b) => a - b);
    let start, end, val;
    const l = sortedStops.length;
    
    if (l === 1) {
      return convertedStops[sortedStops[0]];
    }
    
    // Wenn der Wert kleiner als der kleinste Stop ist
    if (state < sortedStops[0]) {
      return convertedStops[sortedStops[0]];
    }
    
    // Wenn der Wert größer als der größte Stop ist
    if (state > sortedStops[l - 1]) {
      return convertedStops[sortedStops[l - 1]];
    }
    
    for (let i = 0; i < l - 1; i++) {
      const s1 = sortedStops[i];
      const s2 = sortedStops[i + 1];
      if (state >= s1 && state <= s2) {
        [start, end] = [convertedStops[s1], convertedStops[s2]];
        val = this._calculateValueBetween(s1, s2, state);
        return this._getGradientValue(start, end, val);
      }
    }
    
    // Dieser Code sollte nie erreicht werden, aber als Fallback
    return convertedStops[sortedStops[0]];
  }

  _calculateValueBetween(start, end, val) {
    return (val - start) / (end - start);
  }

  _getGradientValue(colorA, colorB, val) {
    const v1 = 1 - val;
    const v2 = val;
    const decA = this._hexColorToDecimal(colorA);
    const decB = this._hexColorToDecimal(colorB);
    const rDec = Math.floor((decA[0] * v1) + (decB[0] * v2));
    const gDec = Math.floor((decA[1] * v1) + (decB[1] * v2));
    const bDec = Math.floor((decA[2] * v1) + (decB[2] * v2));
    const rHex = this._padZero(rDec.toString(16));
    const gHex = this._padZero(gDec.toString(16));
    const bHex = this._padZero(bDec.toString(16));
    return `#${rHex}${gHex}${bHex}`;
  }

  _hexColorToDecimal(color) {
    if (color.startsWith('rgb')) {
      const rgb = color.match(/\d+/g).map(Number);
      return rgb.slice(0, 3);
    }
    
    if (!color.startsWith('#')) {
      const ctx = document.createElement('canvas').getContext('2d');
      ctx.fillStyle = color;
      color = ctx.fillStyle;
    }

    let c = color.substr(1);
    if (c.length === 3) {
      c = `${c[0]}${c[0]}${c[1]}${c[1]}${c[2]}${c[2]}`;
    }

    const [r, g, b] = c.match(/.{2}/g);
    return [parseInt(r, 16), parseInt(g, 16), parseInt(b, 16)];
  }

  _padZero(val) {
    if (val.length < 2) {
      val = `0${val}`;
    }
    return val.substr(0, 2);
  }

  _fire(type, detail) {
    const event = new Event(type, {
      bubbles: true,
      cancelable: false,
      composed: true
    });
    event.detail = detail || {};
    this.shadowRoot.dispatchEvent(event);
    return event;
  }

  _getUnitLabel() {
    if (this.config.show_max) {
      return html`&nbsp;/ ${this.config.attribute_max ? this.state.attributes[this.config.attribute_max] : this.config.max}`;
    } else if (this.config.units) {
      return this.config.units;
    } else if (this.state?.attributes?.unit_of_measurement) {
      return this.state.attributes.unit_of_measurement;
    } else {
      return '';
    }
  }

  _computeIconStyles() {
    const styles = { ...this.config.icon_style } || {};
    
    if (this.state && this.config.icon_color_stops && Object.keys(this.config.icon_color_stops).length > 0 && this._hass) {
      const value = this.config.attribute 
        ? this.state.attributes[this.config.attribute] 
        : this.state.state;
      
      let iconStops = {};
      Object.entries(this.config.icon_color_stops).forEach(([key, value]) => {
        iconStops[key] = value;
      });
      
      styles.color = this._calculateStrokeColor(value, iconStops, true, this._hass);
    }
    
    return Object.entries(styles)
      .map(([key, value]) => `${key}: ${value}`)
      .join(';');
  }

  _renderContent() {
    const rotationStyle = this.config.icon_style?.animation 
      ? Object.entries(this.config.icon_style.animation)
          .map(([key, value]) => `--rotation-${key}: ${value}`)
          .join(';')
      : '';

    const icon = this.config.icon ? html`
      <ha-icon
        class="icon ${this.config.icon_style?.animation ? 'rotating' : ''}"
        .icon="${this.config.icon}"
        style="${this._computeIconStyles()}; ${rotationStyle}"
      ></ha-icon>
    ` : '';

    const name = this.config.name != null ? html`<span id="name">${this.config.name}</span>` : '';
    
    const value = html`
      <span class="text">
        ${this.config.attribute ? this.state.attributes[this.config.attribute] : this._getStateValue()}
      </span>
      <span class="unit">
        ${this._getUnitLabel()}
      </span>
    `;

    switch(this.config.icon_position) {
      case 'middle':
        return html`
          ${name}
          ${icon}
          <span id="label" class="${!!this.config.name ? 'bold' : ''}">
            ${value}
          </span>
        `;
      case 'above':
        return html`
          ${icon}
          ${name}
          <span id="label" class="${!!this.config.name ? 'bold' : ''}">
            ${value}
          </span>
        `;
      case 'below':
        return html`
          ${name}
          <span id="label" class="${!!this.config.name ? 'bold' : ''}">
            ${value}
          </span>
          ${icon}
        `;
      case 'right':
        return html`
          ${name}
          <span id="label" class="${!!this.config.name ? 'bold' : ''}">
            ${value}${icon}
          </span>
        `;
      default: // 'left'
        return html`
          ${name}
          <span id="label" class="${!!this.config.name ? 'bold' : ''}">
            ${icon}${value}
          </span>
        `;
    }
  }

  _getStateValue() {
    if (this.state === undefined) {
      return 0;
    }
    const value = Number(this.state.state);
    return this.config.decimals !== undefined 
      ? value.toFixed(this.config.decimals) 
      : value;
  }

  updated(changedProps) {
    super.updated(changedProps);
    if (changedProps.has('config')) {
      this._applyConfig();
      // Set no-card attribute based on show_card config
      if (this.config.show_card === false) {
        this.setAttribute('no-card', '');
      } else {
        this.removeAttribute('no-card');
      }
    }
  }

  _getValue(value, hass) {
    if (!value) return 0;
    
    if (typeof value === 'string') {
      // Prüfen auf arithmetische Operationen mit Sensoren
      if (value.includes('sensor:') && (value.includes('+') || value.includes('-'))) {
        const parts = value.match(/sensor:([^+\-]+)([\+\-])([\d.]+)/);
        if (parts) {
          const [, entityId, operator, number] = parts;
          const baseValue = Number(hass?.states[entityId.trim()]?.state) || 0;
          const offset = parseFloat(number);
          return operator === '+' ? baseValue + offset : baseValue - offset;
        }
      }
      
      // Normale Sensor-Referenz
      if (value.startsWith('sensor:')) {
        const entityId = value.substr(7);
        return Number(hass?.states[entityId]?.state) || 0;
      }
      
      // Attribut-Referenz
      if (value.startsWith('attr:')) {
        const attr = value.substr(5);
        return Number(this.state?.attributes[attr]) || 0;
      }
      
      return parseFloat(value) || 0;
    }
    
    return Number(value) || 0;
  }

  // Neue Hilfsfunktion für Farbmanipulation
  _adjustColor(color, percent) {
    const rgb = this._hexColorToDecimal(color);
    const adjusted = rgb.map(c => {
      const adj = Math.floor(c * (1 + percent/100));
      return Math.min(255, Math.max(0, adj));
    });
    return `rgb(${adjusted.join(',')})`;
  }

  // Gemeinsame Funktion für die Farbaktualisierung
  _updateCircleColor(state, colorStops, hass) {
    const circle = this.shadowRoot?.querySelector('#circle');
    if (!circle) return;

    const stroke = this._calculateStrokeColor(state, colorStops, false, hass);
    
    if (this.config.use_gradient) {
      // Immer den Gradienten aktualisieren
      const gradientColor1 = stroke;
      const gradientColor2 = this._adjustColor(stroke, 20);
      this.shadowRoot.querySelector('#svg').style.setProperty('--gradient-color-1', gradientColor1);
      this.shadowRoot.querySelector('#svg').style.setProperty('--gradient-color-2', gradientColor2);
      // Sicherstellen, dass der Gradient verwendet wird
      circle.setAttribute('stroke', 'url(#circle-gradient)');
    } else {
      // Normale Farbe setzen
      circle.setAttribute('stroke', stroke);
    }
  }

  // Neue Hilfsfunktion zum Extrahieren des Basis-Sensorwerts
  _getBaseSensorValue(value, hass) {
    if (typeof value === 'string' && value.startsWith('sensor:')) {
      const match = value.match(/sensor:([^+\-]+)/);
      if (match) {
        const entityId = match[1].trim();
        return Number(hass?.states[entityId]?.state) || 0;
      }
    }
    return this._getValue(value, hass);
  }
}
customElements.define('circle-sensor-card', CircleSensorCard);

