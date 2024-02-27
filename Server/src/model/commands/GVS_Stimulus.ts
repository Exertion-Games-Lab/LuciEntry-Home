import Command from "../core/command/Command";
import { CommandName } from "../core/command/CommandNames";
import StartTACS from "../instructions/StartTACS";
import StopTACS from "../instructions/StopTACS";
import Wait from "../instructions/Wait";

class GVS_Stimulation extends Command {

    public millis?: number;
    public intensity?: number;

    public constructor(millis?: number, intensity?: number){

        super(CommandName.GVS_STIMULATION, []);
        
        this.generateInstructions(millis, intensity);
        this.millis = millis;
        this.intensity = intensity;
    }

    public generateInstructions(millis?: number, intensity?: number){
        const instructions = [];

        instructions.push(new StartTACS(intensity || 100));
        instructions.push(new Wait(millis || 10000));
        instructions.push(new StopTACS());

        this.instructions = instructions;
    }

    public setPayload(payload: any): void {
        if (typeof payload !== "object") return;

        if ('millis' in payload){
            if (typeof payload.millis === "number"){
                this.millis = payload.millis;
            } else {
                console.error("Brightness must be of type number")
            }
        }

        if ('intensity' in payload){
            if (typeof payload.intensity === "number"){
                this.intensity = payload.intensity;
            } else {
                console.error("Brightness must be of type number")
            }
        }

        this.generateInstructions();
    }

    public clone(): GVS_Stimulation {
        return new GVS_Stimulation(this.millis, this.intensity);
    }

}

export default GVS_Stimulation;
