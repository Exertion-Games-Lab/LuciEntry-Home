import VisualStimulation from "../../commands/VisualStimulation";
import { CommandName } from "./CommandNames";
import Command from "./Command";
import TacsStimululation from "../../commands/TacsStimulation";
import GVS_Stimulation from "../../commands/GVS_Stimulus";
import AirPump from "../../commands/AirPump";
import Audio from "../../commands/Audio";

const CommandMap: Map<string, Command> = new Map();

CommandMap.set(CommandName.VISUAL_STIMULUS, new VisualStimulation());
CommandMap.set(CommandName.TACS_STIMULUS, new TacsStimululation());
CommandMap.set(CommandName.GVS_STIMULATION, new GVS_Stimulation());
CommandMap.set(CommandName.AUIDO, new Audio());
CommandMap.set(CommandName.AIR_PUMP, new AirPump());
// Add your commands here

export default CommandMap;
