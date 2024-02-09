import Command from "../core/command/Command";
import { CommandName } from "../core/command/CommandNames";
import TurnOffLED from "../instructions/TurnOffLED";
import TurnOnLED from "../instructions/TurnOnLED";
import Wait from "../instructions/Wait";

class GVS_Stimulation extends Command {

    private millis: number;
    private intensity: number;

    public constructor(millis: number = 10000){
        super(CommandName.GVS_STIMULATION, []);
        this.millis = millis;
        this.intensity = intensity;
        this.generateInstructions();
    }

    public clone(): Command {
        return new GVS_Stimulation(this.millis);
    }

    public generateInstructions(){
        this.instructions = [
            new StartTACS(this.intensity),
            new Wait(this.millis),
            new StopTACS()
        ]
    }

    public setPayload(payload: any): void {
        if (typeof payload === "object"){
            if ('millis' in payload){
                if (typeof payload.millis === "number"){
                    this.millis = payload.millis;
                }else{
                    console.error("Millis must be of type number")
                }
            }
        }
        if ('intensity' in payload){
            if (typeof payload.intensity === "number"){
                this.intensity = payload.intensity;
            } else {
                console.error("intensity must be of type number")
            }
        }

        this.generateInstructions();
    }

}

export default GVS_Stimulation;
