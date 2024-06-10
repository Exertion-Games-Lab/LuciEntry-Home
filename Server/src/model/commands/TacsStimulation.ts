import Command from "../core/command/Command";
import Wait from "../instructions/Wait";
import StartTACS from "../instructions/StartTACS";
import StopTACS from "../instructions/StopTACS";
import { CommandName } from "../core/command/CommandNames";
import { StartProgram } from "../instructions/StartProgram";
import { StopProgram } from "../instructions/StopProgram";

class TacsStimululation extends Command {

    public intensity?: number;
    public frequency?: number;
    public millis?: number;

    public constructor(programNumber?: number, millis?: number, intensity?: number, frequency?: number){
        const num = programNumber || 0;
        super(CommandName.TACS_STIMULUS, [
            new StartProgram(num),
            new Wait(10000),
            new StopProgram(num)
        ]);

        this.generateInstructions(millis, intensity, frequency);
        this.millis = millis;
        this.intensity = intensity;
        this.frequency = frequency;
    }

    public generateInstructions(millis?: number, intensity?: number, frequency?: number){
        const instructions = [];
        instructions.push(new StartTACS(intensity || 100, frequency || 100));
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
                console.error("Millis must be of type number")
            }
        }

        if ('intensity' in payload){
            if (typeof payload.intensity === "number"){
                this.intensity = payload.intensity;
            } else {
                console.error("Intensity must be of type number")
            }
        }

        if ('frequency' in payload){
            if (typeof payload.frequency === "number"){
                this.frequency = payload.frequency;
            } else {
                console.error("Frequency must be of type number")
            }
        }

        this.generateInstructions(this.millis, this.intensity, this.frequency);

    }

    public clone(): TacsStimululation {
        return new TacsStimululation(
            this.millis,
            this.intensity,
            this.frequency
        )
    }
}

export default TacsStimululation;