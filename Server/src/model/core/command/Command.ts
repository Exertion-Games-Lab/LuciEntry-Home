import { CommandName } from "./CommandNames";
import Instruction from "../instruction/Instruction";

/**
 * This is our command class, it groups together instructions so that they can be sent as a batch to a device.
 */
abstract class Command {

    public readonly id: string;
    public readonly name: CommandName;
    public instructions: Instruction<any>[];   // The instructions can have any payload
    public noOfInstructions: number;

    public constructor(name: CommandName, instructions: Instruction<any>[]){
        this.id = Math.random().toString(36).substr(2, 9); // TODO: this is not actually unique, should work for our purposes though
        this.name = name;
        this.instructions = instructions;
        this.noOfInstructions = instructions.length
    }

    abstract clone(): Command;
    abstract setPayload(payload: any): void;
}

export default Command;
