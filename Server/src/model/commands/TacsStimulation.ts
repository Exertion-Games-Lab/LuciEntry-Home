import Command from "../core/command/Command";
import Wait from "../instructions/Wait";
import { CommandName } from "../core/command/CommandNames";
import { StartProgram } from "../instructions/StartProgram";
import { StopProgram } from "../instructions/StopProgram";

class TacsStimululation extends Command {

    public constructor(programNumber?: number){
        const num = programNumber || 0;
        super(CommandName.TACS_STIMULUS, [
            new StartProgram(num),
            new Wait(10000),
            new StopProgram(num)
        ]);
    }

    public setPayload(payload: any): void {
        // TODO
    }

    public clone(): TacsStimululation {
        // TODO
        return new TacsStimululation(0)
    }
}

export default TacsStimululation;