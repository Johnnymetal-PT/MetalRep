import { registry } from "@web/core/registry";
import { deserializeDateTime } from "@web/core/l10n/dates";
const { DateTime } = luxon;

// ─── Offer Timer Service ─────────────────────────────────────────────────
export const OfferTimerService = {
    start() {
        return {
            create(params) {
                if (params.offerDate !== undefined && params.offerDate !== 'false'){
                    let offerTime = deserializeDateTime(params.offerDate);
                    let currentTime = DateTime.now();
                    let duration = offerTime.ts - currentTime.ts;
                    if (duration < 0) {
                        let storedTimerInfo = sessionStorage.getItem("as_timer_ids");
                        if (storedTimerInfo) {
                            let storedTimerIds = JSON.parse(storedTimerInfo);
                            storedTimerIds.forEach(intervalId => {
                                clearInterval(intervalId);
                            });
                        }
                        sessionStorage.removeItem("as_timer_ids");
                        params.target.innerHTML = '';
                    }
                    else {
                        let days = Math.floor(duration / (1000 * 60 * 60 * 24));
                        let hours = Math.floor((duration / (1000 * 60 * 60)) % 24);
                        let minutes = Math.floor((duration / 1000 / 60) % 60);
                        let seconds = Math.floor((duration / 1000) % 60);
                        days = days < 10 ? "0" + days : days;
                        hours = hours < 10 ? "0" + hours : hours;
                        minutes = minutes < 10 ? "0" + minutes : minutes;
                        seconds = seconds < 10 ? "0" + seconds : seconds;
                        params.target.closest(".as-offer-timer")?.classList.remove("d-none");
                        params.target.innerHTML = `<ul><li class="as-timer-label">Offer ends in</li>
                                 <li><label>${days}</label><em>d</em><span>Days</span></li>
                                 <li><label>${hours}</label><em>h</em><span>Hours</span></li>
                                 <li><label>${minutes}</label><em>m</em><span>Minutes</span></li>
                                 <li><label>${seconds}</label><em>s</em><span>Seconds</span></li>
                             </ul>`;
                    }

                }
            }
        }
    },

};
registry.category("services").add("offer_timer", OfferTimerService);
