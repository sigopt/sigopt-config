import readline from "readline";

import ConfigBroker from "../src/js/sigopt_config/broker";

const readlineInterface = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false,
});

let dispatchP = Promise.resolve(null);
let configBroker = null;

const loadConfigBroker = ({directory}) => {
  dispatchP = dispatchP.then(() => ConfigBroker.fromDirectory(directory).then((broker) => new Promise((success, error) =>
    broker.initialize(
      () => {
        configBroker = broker;
        console.log(JSON.stringify({message: `Loaded broker from ${directory}`}));
        return success(null);
      },
      error,
    )
  ),
    (err) => {
      console.log(JSON.stringify({error: `Error loading broker from ${directory}: ${err}`}));
      console.error(err);
    },
  ));
};

const readConfigBroker = ({method, key}) => {
  dispatchP = dispatchP.then(() => {
    if (!configBroker) {
      console.log(JSON.stringify({error: `Error reading from broker: broker not loaded`}));
      return;
    }
    const getConfig = ({
      get: configBroker.get,
      get_object: configBroker.getObject,
    })[method];
    if (!getConfig) {
      console.log(JSON.stringify({error: `Error reading from broker: unknown method: ${method}`}));
      return;
    }
    try {
      const value = getConfig.bind(configBroker)(key);
      console.log(JSON.stringify({value}));
      return;
    } catch (err) {
      console.log(JSON.stringify({error: `Error reading from broker: ${err}`}));
      console.error(err);
      return;
    }
  });
};

const resetConfigBroker = () => {
  dispatchP.then(() => {
    configBroker = null;
    console.log(JSON.stringify({message: "Reset the broket, ready to load"}));
  });
};

readlineInterface.on("line", (line) => {
  let command;
  try {
    command = JSON.parse(line);
  } catch (err) {
    console.log(JSON.stringify({error: `Could not parse JSON command: ${command}`}));
    console.error(err);
    return;
  }
  const dispatch = ({
    load: loadConfigBroker,
    read: readConfigBroker,
    reset: resetConfigBroker,
    done: () => {
      console.log(JSON.stringify({}));
      process.exit();
    },
  })[command.command];
  dispatch(command);
});
