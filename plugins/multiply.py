# Cryptonote core:  Bytecoin
# Allows users to create their own networks on top of a proven core
# Adds various parameters to command line

import fileinput
import sys
import re
import json
import argparse
import textwrap
import os
import shutil

parser = argparse.ArgumentParser()

parser.add_argument('--config', action='store', dest='config_file',
                    default='config.json',
                    help='Configuration filename. Format: json'
                    )
parser.add_argument('--source', action='store', dest='source',
                    default='tmp',
                    help='Working folder containing the base coin source'
                    )
args = parser.parse_args()

json_data = open(args.config_file)
config = json.load(json_data)
json_data.close()

paths = {}
source_paths = {}


# Common text blocks
# Common command line arguments added to daemon and simplewallet
common_command_line_descriptors = textwrap.dedent("""\
  const command_line::arg_descriptor<std::string> arg_GENESIS_COINBASE_TX_HEX  = {"GENESIS_COINBASE_TX_HEX", "Genesis transaction hex", CryptoNote::parameters::GENESIS_COINBASE_TX_HEX};  
  const command_line::arg_descriptor<uint64_t>    arg_CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX  = {"CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX", "uint64_t", CryptoNote::parameters::CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX};
  const command_line::arg_descriptor<uint64_t>    arg_MONEY_SUPPLY  = {"MONEY_SUPPLY", "uint64_t", CryptoNote::parameters::MONEY_SUPPLY};
  const command_line::arg_descriptor<unsigned int>    arg_EMISSION_SPEED_FACTOR  = {"EMISSION_SPEED_FACTOR", "unsigned int", CryptoNote::parameters::EMISSION_SPEED_FACTOR};
  const command_line::arg_descriptor<uint64_t>    arg_CRYPTONOTE_BLOCK_GRANTED_FULL_REWARD_ZONE  = {"CRYPTONOTE_BLOCK_GRANTED_FULL_REWARD_ZONE", "uint64_t", CryptoNote::parameters::CRYPTONOTE_BLOCK_GRANTED_FULL_REWARD_ZONE};
  const command_line::arg_descriptor<uint64_t>    arg_CRYPTONOTE_DISPLAY_DECIMAL_POINT  = {"CRYPTONOTE_DISPLAY_DECIMAL_POINT", "size_t", CryptoNote::parameters::CRYPTONOTE_DISPLAY_DECIMAL_POINT};
  const command_line::arg_descriptor<uint64_t>    arg_MINIMUM_FEE  = {"MINIMUM_FEE", "uint64_t", CryptoNote::parameters::MINIMUM_FEE};
  const command_line::arg_descriptor<uint64_t>    arg_DEFAULT_DUST_THRESHOLD  = {"DEFAULT_DUST_THRESHOLD", "uint64_t", CryptoNote::parameters::DEFAULT_DUST_THRESHOLD};
  const command_line::arg_descriptor<uint64_t>    arg_DIFFICULTY_TARGET  = {"DIFFICULTY_TARGET", "uint64_t", CryptoNote::parameters::DIFFICULTY_TARGET};
  const command_line::arg_descriptor<size_t>      arg_CRYPTONOTE_MINED_MONEY_UNLOCK_WINDOW  = {"CRYPTONOTE_MINED_MONEY_UNLOCK_WINDOW", "size_t", CryptoNote::parameters::CRYPTONOTE_MINED_MONEY_UNLOCK_WINDOW};
  const command_line::arg_descriptor<uint64_t>    arg_MAX_BLOCK_SIZE_INITIAL  = {"MAX_BLOCK_SIZE_INITIAL", "uint64_t", CryptoNote::parameters::MAX_BLOCK_SIZE_INITIAL};
  const command_line::arg_descriptor<uint64_t>    arg_EXPECTED_NUMBER_OF_BLOCKS_PER_DAY  = {"EXPECTED_NUMBER_OF_BLOCKS_PER_DAY", "uint64_t"};
  const command_line::arg_descriptor<uint64_t>    arg_UPGRADE_HEIGHT  = {"UPGRADE_HEIGHT", "uint64_t", 0};
  const command_line::arg_descriptor<size_t>      arg_DIFFICULTY_CUT  = {"DIFFICULTY_CUT", "uint64_t", CryptoNote::parameters::DIFFICULTY_CUT};
  const command_line::arg_descriptor<size_t>      arg_DIFFICULTY_LAG  = {"DIFFICULTY_LAG", "uint64_t", CryptoNote::parameters::DIFFICULTY_LAG};
""")
common_command_line_args = textwrap.dedent("""\
  command_line::add_arg(desc_cmd_sett, arg_GENESIS_COINBASE_TX_HEX);
  command_line::add_arg(desc_cmd_sett, arg_CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX);
  command_line::add_arg(desc_cmd_sett, arg_MONEY_SUPPLY);
  command_line::add_arg(desc_cmd_sett, arg_EMISSION_SPEED_FACTOR);
  command_line::add_arg(desc_cmd_sett, arg_CRYPTONOTE_BLOCK_GRANTED_FULL_REWARD_ZONE);
  command_line::add_arg(desc_cmd_sett, arg_CRYPTONOTE_DISPLAY_DECIMAL_POINT);
  command_line::add_arg(desc_cmd_sett, arg_MINIMUM_FEE);
  command_line::add_arg(desc_cmd_sett, arg_DEFAULT_DUST_THRESHOLD);
  command_line::add_arg(desc_cmd_sett, arg_DIFFICULTY_TARGET);
  command_line::add_arg(desc_cmd_sett, arg_CRYPTONOTE_MINED_MONEY_UNLOCK_WINDOW);
  command_line::add_arg(desc_cmd_sett, arg_MAX_BLOCK_SIZE_INITIAL);
  command_line::add_arg(desc_cmd_sett, arg_EXPECTED_NUMBER_OF_BLOCKS_PER_DAY);
  command_line::add_arg(desc_cmd_sett, arg_UPGRADE_HEIGHT);
  command_line::add_arg(desc_cmd_sett, arg_DIFFICULTY_CUT);
  command_line::add_arg(desc_cmd_sett, arg_DIFFICULTY_LAG);
""")
currencyBuilder_params = textwrap.dedent("""\
  currencyBuilder.genesisCoinbaseTxHex(command_line::get_arg(vm, arg_GENESIS_COINBASE_TX_HEX));
  currencyBuilder.publicAddressBase58Prefix(command_line::get_arg(vm, arg_CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX));
  currencyBuilder.moneySupply(command_line::get_arg(vm, arg_MONEY_SUPPLY));
  currencyBuilder.emissionSpeedFactor(command_line::get_arg(vm, arg_EMISSION_SPEED_FACTOR));
  currencyBuilder.blockGrantedFullRewardZone(command_line::get_arg(vm, arg_CRYPTONOTE_BLOCK_GRANTED_FULL_REWARD_ZONE));
  currencyBuilder.numberOfDecimalPlaces(command_line::get_arg(vm, arg_CRYPTONOTE_DISPLAY_DECIMAL_POINT));
  currencyBuilder.mininumFee(command_line::get_arg(vm, arg_MINIMUM_FEE));
  currencyBuilder.defaultDustThreshold(command_line::get_arg(vm, arg_DEFAULT_DUST_THRESHOLD));
  currencyBuilder.difficultyTarget(command_line::get_arg(vm, arg_DIFFICULTY_TARGET));
  currencyBuilder.minedMoneyUnlockWindow(command_line::get_arg(vm, arg_CRYPTONOTE_MINED_MONEY_UNLOCK_WINDOW));
  currencyBuilder.maxBlockSizeInitial(command_line::get_arg(vm, arg_MAX_BLOCK_SIZE_INITIAL));

  if (command_line::has_arg(vm, arg_EXPECTED_NUMBER_OF_BLOCKS_PER_DAY) && command_line::get_arg(vm, arg_EXPECTED_NUMBER_OF_BLOCKS_PER_DAY) != 0)
  {
    currencyBuilder.difficultyWindow(command_line::get_arg(vm, arg_EXPECTED_NUMBER_OF_BLOCKS_PER_DAY));
    currencyBuilder.upgradeVotingWindow(command_line::get_arg(vm, arg_EXPECTED_NUMBER_OF_BLOCKS_PER_DAY));
    currencyBuilder.upgradeWindow(command_line::get_arg(vm, arg_EXPECTED_NUMBER_OF_BLOCKS_PER_DAY));
  } else {
    currencyBuilder.difficultyWindow(24 * 60 * 60 / command_line::get_arg(vm, arg_DIFFICULTY_TARGET));
  }
  currencyBuilder.maxBlockSizeGrowthSpeedDenominator(365 * 24 * 60 * 60 / command_line::get_arg(vm, arg_DIFFICULTY_TARGET));
  currencyBuilder.lockedTxAllowedDeltaSeconds(command_line::get_arg(vm, arg_DIFFICULTY_TARGET) * CryptoNote::parameters::CRYPTONOTE_LOCKED_TX_ALLOWED_DELTA_BLOCKS);  

  if (command_line::has_arg(vm, arg_UPGRADE_HEIGHT) && command_line::get_arg(vm, arg_UPGRADE_HEIGHT) != 0)
  {
    currencyBuilder.upgradeHeight(command_line::get_arg(vm, arg_UPGRADE_HEIGHT));
  }

  currencyBuilder.difficultyLag(command_line::get_arg(vm, arg_DIFFICULTY_CUT));
  currencyBuilder.difficultyCut(command_line::get_arg(vm, arg_DIFFICULTY_LAG));
""")

####
# Text added to src/cryptonote_config.h
cryptonote_config_params = textwrap.dedent("""\
const char     GENESIS_COINBASE_TX_HEX[]                        = "010a01ff0001ffffffffffff0f029b2e4c0281c0b02e7c53291a94d1d0cbff8883f8024f5142ee494ffbbd08807121013c086a48c15fb637a96991bc6d53caf77068b5ba6eeb3c82357228c49790584a";
    """)

# Make changes in src/cryptonote_config.h
paths['cryptonote_config'] = args.source + "/src/cryptonote_config.h"

for line in fileinput.input([paths['cryptonote_config']], inplace=True):
    if "} // parameters" in line:
        sys.stdout.write(cryptonote_config_params)
    # sys.stdout is redirected to the file
    sys.stdout.write(line)

GENESIS_COINBASE_TX_HEX_re = re.compile(r"(const char\s+GENESIS_COINBASE_TX_HEX\[\]\s+=)\s+\"\w+\"", re.IGNORECASE)

for line in fileinput.input([paths['cryptonote_config']], inplace=True):
    line = GENESIS_COINBASE_TX_HEX_re.sub("\\1 \"%s\"" % config['core']['GENESIS_COINBASE_TX_HEX'], line)
    # sys.stdout is redirected to the file
    sys.stdout.write(line)

####
# Text added to src/daemon/daemon.cpp
# Add CHECKPOINT command line ability
daemon_populate_declare_checkpoints = textwrap.dedent("""\
std::vector<CryptoNote::CheckpointData> checkpoint_input;
std::vector<std::string> checkpoint_args = command_line::get_arg(vm, arg_CHECKPOINT);
std::vector<std::string> checkpoint_blockIds;

if (command_line::has_arg(vm, arg_CHECKPOINT) && checkpoint_args.size() != 0)
{
  for(const std::string& str: checkpoint_args) {
    std::string::size_type p = str.find(':');
    if(p != std::string::npos)
    {
      uint64_t checkpoint_height = std::stoull(str.substr(0, p));
      checkpoint_blockIds.push_back(str.substr(p+1, str.size()));
      checkpoint_input.push_back({ checkpoint_height, checkpoint_blockIds.back().c_str() });
    }
  }
}
else
{
  if (!command_line::has_arg(vm, arg_UPGRADE_HEIGHT) || command_line::get_arg(vm, arg_UPGRADE_HEIGHT) == 0 || command_line::get_arg(vm, arg_UPGRADE_HEIGHT) == 1) {
      checkpoint_input = CryptoNote::CHECKPOINTS;
  }
}
    """)

daemon_command_line_descriptors = textwrap.dedent("""\
  const command_line::arg_descriptor<std::string> arg_CRYPTONOTE_NAME  = {"CRYPTONOTE_NAME", "Cryptonote name. Used for storage directory", ""};
  const command_line::arg_descriptor< std::vector<std::string> > arg_CHECKPOINT  = {"CHECKPOINT", "Checkpoints. Format: HEIGHT:HASH"};
    """)

daemon_command_line_args = textwrap.dedent("""\
  command_line::add_arg(desc_cmd_sett, arg_CRYPTONOTE_NAME);
  command_line::add_arg(desc_cmd_sett, arg_CHECKPOINT);
    """)

# Add configurable default directories
daemon_cryptonote_name_includes = textwrap.dedent("""\
  #include <boost/algorithm/string.hpp>
    """)

daemon_default_data_dir = textwrap.dedent("""\
  std::string default_data_dir = tools::get_default_data_dir();
  if (command_line::has_arg(vm, arg_CRYPTONOTE_NAME) && !command_line::get_arg(vm, arg_CRYPTONOTE_NAME).empty()) {
    boost::replace_all(default_data_dir, CryptoNote::CRYPTONOTE_NAME, command_line::get_arg(vm, arg_CRYPTONOTE_NAME));
  }
  coreConfig.configFolder = default_data_dir;
  netNodeConfig.configFolder = default_data_dir;
    """)

# Print-genesis-tx improvements
daemon_print_genesis_tx = "CryptoNote::CurrencyBuilder currencyBuilder(logManager);\n" + currencyBuilder_params + "CryptoNote::Transaction tx = currencyBuilder.generateGenesisTransaction();\n" 

daemon_print_genesis_tx_config_text = textwrap.dedent("""\
  std::cout << "GENESIS_COINBASE_TX_HEX=" << tx_hex << std::endl;
    """)

# Make changes in src/daemon/daemon.cpp
paths['daemon'] = args.source + "/src/daemon/daemon.cpp"

for line in fileinput.input([paths['daemon']], inplace=True):
    if "const command_line::arg_descriptor<std::string> arg_config_file" in line:
        line = 'const command_line::arg_descriptor<std::string> arg_config_file = {"config-file", "Specify configuration file", "./configs/-.conf"};\n'
    if "for (const auto& cp : CryptoNote::CHECKPOINTS) {" in line:
        line = "for (const auto& cp : checkpoint_input) {\n"
    if "arg_testnet_on" in line and "= {" in line:
        sys.stdout.write(common_command_line_descriptors)
        sys.stdout.write(daemon_command_line_descriptors)
    if "#include <boost/program_options.hpp>" in line:
        sys.stdout.write(daemon_cryptonote_name_includes)
    # Allow undeclared options in config
    if "po::store(po::parse_config_file<char>(config_path.string<std::string>().c_str(), desc_cmd_sett), vm);" in line:
        line = "po::store(po::parse_config_file<char>(config_path.string<std::string>().c_str(), desc_cmd_sett, true), vm);"
    # If print-genesis-tx module is present
    if "print-genesis-tx.py" in config['plugins']:
        if "CryptoNote::Transaction tx = CryptoNote::CurrencyBuilder(logManager).generateGenesisTransaction();" in line:
            line = daemon_print_genesis_tx;
        if "std::cout << \"const char GENESIS_COINBASE_TX_HEX[] = \" << tx_hex << \";\" << std::endl;" in line:
            line = daemon_print_genesis_tx_config_text
    # sys.stdout is redirected to the file
    sys.stdout.write(line)
    if "command_line::add_arg(desc_cmd_sett, arg_testnet_on);" in line:
        sys.stdout.write(common_command_line_args)
        sys.stdout.write(daemon_command_line_args)
    if "CryptoNote::CurrencyBuilder currencyBuilder(logManager);" in line:
        sys.stdout.write(currencyBuilder_params)
    if "CryptoNote::checkpoints checkpoints(logManager);" in line:
        sys.stdout.write(daemon_populate_declare_checkpoints)
    if "minerConfig.init(vm);" in line:
        sys.stdout.write(daemon_default_data_dir)

####
# Add GENESIS_COINBASE_TX_HEX command line ability
# Text added to src/cryptonote_core/Currency.h
currency_vars = textwrap.dedent("""\
    std::string m_genesisCoinbaseTxHex;
    """)
currency_builder_params = textwrap.dedent("""\
    CurrencyBuilder& genesisCoinbaseTxHex(const std::string& val) { m_currency.m_genesisCoinbaseTxHex = val; return *this; }
    """)

# Make changes in src/cryptonote_core/Currency.h
paths['currency_h'] = args.source + "/src/cryptonote_core/Currency.h"

for line in fileinput.input([paths['currency_h']], inplace=True):
    if "testnet" in line and "return *this" in line:
        sys.stdout.write(currency_builder_params)
    # sys.stdout is redirected to the file
    sys.stdout.write(line)
    if "bool m_testnet;" in line:
        sys.stdout.write(currency_vars)

###
# Make changes in src/cryptonote_core/Currency.cpp
paths['currency_cpp'] = args.source + "/src/cryptonote_core/Currency.cpp"

GENESIS_COINBASE_TX_HEX_re = re.compile(r"(std::string genesisCoinbaseTxHex =) \"\S+\";", re.IGNORECASE)
GENESIS_COINBASE_TX_HEX_var_name = "m_genesisCoinbaseTxHex"
for line in fileinput.input([paths['currency_cpp']], inplace=True):
    line = GENESIS_COINBASE_TX_HEX_re.sub("\\1 %s;" % GENESIS_COINBASE_TX_HEX_var_name, line)
    # sys.stdout is redirected to the file
    sys.stdout.write(line)

####
# Add config file reading ability to simplewallet
# Looks stable
# Text added to src/simplewallet/simplewallet.cpp
simplewallet_command_line_descriptors = textwrap.dedent("""\
  const command_line::arg_descriptor<std::string> arg_config_file = {"config-file", "Specify configuration file", "./configs/-.conf"};  
    """)
simplewallet_daemon_port_descriptor = textwrap.dedent("""\
    const command_line::arg_descriptor<std::string> arg_rpc_bind_port = {"rpc-bind-port", "", std::to_string(RPC_DEFAULT_PORT)};
    """)
simplewallet_common_command_line_args = common_command_line_args.replace('desc_cmd_sett', 'desc_params')
simplewallet_command_line_args = textwrap.dedent("""\
  command_line::add_arg(desc_params, command_line::arg_data_dir, tools::get_default_data_dir());
  command_line::add_arg(desc_params, arg_config_file);
    """)
simplewallet_daemon_port_arg = textwrap.dedent("""\
    command_line::add_arg(desc_params, arg_rpc_bind_port);
    """)
simplewallet_config_file_args = textwrap.dedent("""\
    std::string data_dir = command_line::get_arg(vm, command_line::arg_data_dir);
    std::string config = command_line::get_arg(vm, arg_config_file);

      std::cout << config << std::endl;

    boost::filesystem::path data_dir_path(data_dir);
    boost::filesystem::path config_path(config);

      std::cout << "boost filesystem passed" << std::endl;
    if (!config_path.has_parent_path())
    {
      std::cout << "file not found" << std::endl;
      config_path = data_dir_path / config_path;
    }

      std::cout << "boost filesystem passed" << std::endl;
    boost::system::error_code ec;
    if (boost::filesystem::exists(config_path, ec))
    {
      std::cout << "config path exist" << std::endl;
      po::store(po::parse_config_file<char>(config_path.string<std::string>().c_str(), desc_params, true), vm);
    }
    else
    {
      std::cout << "config path does not exist" << std::endl;
    }
    """)

# Make changes in src/simplewallet/simplewallet.cpp
paths['simplewallet'] = args.source + "/src/simplewallet/simplewallet.cpp"

for line in fileinput.input([paths['simplewallet']], inplace=True):
    if "RPC_DEFAULT_PORT" in line:
      line = line.replace("RPC_DEFAULT_PORT", "std::stoi(command_line::get_arg(vm, arg_rpc_bind_port))");
    if "arg_testnet" in line and "= {" in line:
        sys.stdout.write(simplewallet_command_line_descriptors)
        sys.stdout.write(common_command_line_descriptors)
        sys.stdout.write(simplewallet_daemon_port_descriptor)
    if "CryptoNote::Currency currency = CryptoNote::CurrencyBuilder(logManager)." in line:
        line = "CryptoNote::CurrencyBuilder currencyBuilder(logManager);\n"
        line = line + currencyBuilder_params
    if "testnet(command_line::get_arg(vm, arg_testnet)).currency();" in line:
        line = "currencyBuilder.testnet(command_line::get_arg(vm, arg_testnet));\n"
        line = line + "CryptoNote::Currency currency = currencyBuilder.currency();\n"
    # sys.stdout is redirected to the file
    sys.stdout.write(line)
    if "tools::wallet_rpc_server::init_options(desc_params);" in line:
        sys.stdout.write(simplewallet_command_line_args)
        sys.stdout.write(simplewallet_common_command_line_args)
        sys.stdout.write(simplewallet_daemon_port_arg)
    if "po::store(parser.run(), vm);" in line:    # modified a few lines above
        sys.stdout.write(simplewallet_config_file_args)

###
# Make changes in src/wallet/wallet_rpc_server.cpp
paths['wallet_rpc_server'] = args.source + "/src/wallet/wallet_rpc_server.cpp"

wallet_rpc_bind_port_re = re.compile(r"(const command_line::arg_descriptor<uint16_t> wallet_rpc_server::arg_rpc_bind_port = {) \"\S+\"(.*)", re.IGNORECASE)
wallet_rpc_bind_port_var_name = "wallet-rpc-bind-port"
wallet_rpc_bind_ip_re = re.compile(r"(onst command_line::arg_descriptor<std::string> wallet_rpc_server::arg_rpc_bind_ip = {) \"\S+\"(.*)", re.IGNORECASE)
wallet_rpc_bind_ip_var_name = "wallet-rpc-bind-ip"
for line in fileinput.input([paths['wallet_rpc_server']], inplace=True):
    line = wallet_rpc_bind_port_re.sub("\\1 \"%s\"\\2" % wallet_rpc_bind_port_var_name, line)
    line = wallet_rpc_bind_ip_re.sub("\\1 \"%s\"\\2" % wallet_rpc_bind_ip_var_name, line)
    # sys.stdout is redirected to the file
    sys.stdout.write(line)


####
# Text added to src/p2p/NetNodeConfig.h
NetNodeConfig_h_includes = textwrap.dedent("""\
    #include <boost/uuid/uuid.hpp>
    #include <boost/uuid/uuid_io.hpp>
    #include "p2p_networks.h"
    """)
NetNodeConfig_h_vars = textwrap.dedent("""\
    boost::uuids::uuid networkId;
    std::string p2pStatTrustedPubKey;
    """)

# Make changes in src/p2p/NetNodeConfig.h
paths['NetNodeConfig_h'] = args.source + "/src/p2p/NetNodeConfig.h"

for line in fileinput.input([paths['NetNodeConfig_h']], inplace=True):
    if "p2p_protocol_types.h" in line:
        sys.stdout.write(NetNodeConfig_h_includes)
    # sys.stdout is redirected to the file
    sys.stdout.write(line)
    if "bool hideMyPort;" in line:
        sys.stdout.write(NetNodeConfig_h_vars)



# Text added to src/p2p/NetNodeConfig.cpp
NetNodeConfig_cpp_command_line_descriptors = textwrap.dedent("""\
    const command_line::arg_descriptor<std::string> arg_network_id = {"BYTECOIN_NETWORK", "Network id", boost::lexical_cast<std::string>(BYTECOIN_NETWORK)};
    const command_line::arg_descriptor<std::string> arg_P2P_STAT_TRUSTED_PUB_KEY = {"P2P_STAT_TRUSTED_PUB_KEY", "P2P stat trusted pub key", ""};
    """)
NetNodeConfig_cpp_command_line_args = textwrap.dedent("""\
    command_line::add_arg(desc, arg_P2P_STAT_TRUSTED_PUB_KEY);
    command_line::add_arg(desc, arg_network_id);
    """)
NetNodeConfig_cpp_get_args = textwrap.dedent("""\
    p2pStatTrustedPubKey = command_line::get_arg(vm, arg_P2P_STAT_TRUSTED_PUB_KEY);
    networkId = boost::lexical_cast<boost::uuids::uuid>(command_line::get_arg(vm, arg_network_id));
    """)
NetNodeConfig_cpp_vars = textwrap.dedent("""\
  p2pStatTrustedPubKey = "";
    """)

# Make changes in src/p2p/NetNodeConfig.cpp
paths['NetNodeConfig_cpp'] = args.source + "/src/p2p/NetNodeConfig.cpp"

for line in fileinput.input([paths['NetNodeConfig_cpp']], inplace=True):
    if "arg_p2p_hide_my_port" in line and "hide-my-port" in line:
        sys.stdout.write(NetNodeConfig_cpp_command_line_descriptors)
    # sys.stdout is redirected to the file
    sys.stdout.write(line)
    if "command_line::add_arg(desc, arg_p2p_hide_my_port);" in line:
        sys.stdout.write(NetNodeConfig_cpp_command_line_args)
    if "allowLocalIp = command_line::get_arg(vm, arg_p2p_allow_local_ip);" in line:
        sys.stdout.write(NetNodeConfig_cpp_get_args)
    if "hideMyPort = false;" in line:
        sys.stdout.write(NetNodeConfig_cpp_vars)


####
# Text added to src/p2p/net_node.h
net_node_h_vars = textwrap.dedent("""\
    std::string m_p2pStatTrustedPubKey;
    """)

# Make changes in src/p2p/net_node.h
paths['net_node_h'] = args.source + "/src/p2p/net_node.h"
for line in fileinput.input([paths['net_node_h']], inplace=True):
    # sys.stdout is redirected to the file
    sys.stdout.write(line)
    if "boost::uuids::uuid m_network_id;" in line:
        sys.stdout.write(net_node_h_vars)


####
# Text added to src/p2p/net_node.cpp
net_node_cpp_vars = textwrap.dedent("""\
    m_network_id = config.networkId;
    m_p2pStatTrustedPubKey = config.p2pStatTrustedPubKey;
    """)

# Make changes in src/p2p/net_node.cpp
paths['net_node_cpp'] = args.source + "/src/p2p/net_node.cpp"
for line in fileinput.input([paths['net_node_cpp']], inplace=True):
    if "if (!testnet) {" in line:
        line = "    if (!testnet && config.seedNodes.size() == 0) {\n"
    if "Common::podFromHex(CryptoNote::P2P_STAT_TRUSTED_PUB_KEY, pk);" in line:
        line = "    Common::podFromHex(m_p2pStatTrustedPubKey, pk);"
    # sys.stdout is redirected to the file
    sys.stdout.write(line)
    if "m_allow_local_ip = config.allowLocalIp;" in line:
        sys.stdout.write(net_node_cpp_vars)


# Add CoinBaseConfiguration.h src/payment_service/CoinBaseConfiguration.h
paths['CoinBaseConfiguration.h'] = args.source + "/src/payment_service/CoinBaseConfiguration.h"
source_paths['CoinBaseConfiguration.h'] = os.path.dirname(os.path.realpath(__file__)) + '/multiply/CoinBaseConfiguration.h'
if (os.path.isfile(source_paths['CoinBaseConfiguration.h'])):
    shutil.copyfile(source_paths['CoinBaseConfiguration.h'],paths['CoinBaseConfiguration.h'])


# Add CoinBaseConfiguration.cpp src/payment_service/CoinBaseConfiguration.cpp
paths['CoinBaseConfiguration.cpp'] = args.source + "/src/payment_service/CoinBaseConfiguration.cpp"
source_paths['CoinBaseConfiguration.cpp'] = os.path.dirname(os.path.realpath(__file__)) + '/multiply/CoinBaseConfiguration.cpp'
if (os.path.isfile(source_paths['CoinBaseConfiguration.cpp'])):
    shutil.copyfile(source_paths['CoinBaseConfiguration.cpp'],paths['CoinBaseConfiguration.cpp'])


####
# Text added to src/payment_service/ConfigurationManager.h
ConfigurationManager_h_includes = textwrap.dedent("""\
#include "CoinBaseConfiguration.h"
    """)

ConfigurationManager_h_vars = textwrap.dedent("""\
  CoinBaseConfiguration coinBaseConfig;
    """)

# Make changes in src/payment_service/ConfigurationManager.h
paths['ConfigurationManager.h'] = args.source + "/src/payment_service/ConfigurationManager.h"
for line in fileinput.input([paths['ConfigurationManager.h']], inplace=True):
    # sys.stdout is redirected to the file
    sys.stdout.write(line)
    if "#include \"RpcNodeConfiguration.h\"" in line:
        sys.stdout.write(ConfigurationManager_h_includes);
    if "RpcNodeConfiguration remoteNodeConfig;" in line:
        sys.stdout.write(ConfigurationManager_h_vars);


####
# Text added to src/payment_service/ConfigurationManager.cpp
ConfigurationManager_cpp_initOptions = textwrap.dedent("""\
  po::options_description coinBaseOptions("Coin Base Options");
  CoinBaseConfiguration::initOptions(coinBaseOptions);
    """)
ConfigurationManager_cpp_coinBaseConfig_init_confOptions = textwrap.dedent("""\
  coinBaseConfig.init(confOptions);
    """)
ConfigurationManager_cpp_coinBaseConfig_init_cmdOptions = textwrap.dedent("""\
  coinBaseConfig.init(cmdOptions);
    """)

# Make changes in src/payment_service/ConfigurationManager.cpp
paths['ConfigurationManager.cpp'] = args.source + "/src/payment_service/ConfigurationManager.cpp"
for line in fileinput.input([paths['ConfigurationManager.cpp']], inplace=True):
    if "cmdOptionsDesc.add(cmdGeneralOptions).add(remoteNodeOptions).add(netNodeOptions);" in line:
        line = "cmdOptionsDesc.add(cmdGeneralOptions).add(remoteNodeOptions).add(netNodeOptions).add(coinBaseOptions);"
    if "confOptionsDesc.add(confGeneralOptions).add(remoteNodeOptions).add(netNodeOptions);" in line:
        line = "confOptionsDesc.add(confGeneralOptions).add(remoteNodeOptions).add(netNodeOptions).add(coinBaseOptions);"
    # Allow undeclared options in config
    if "po::store(po::parse_config_file(confStream, confOptionsDesc), confOptions);" in line:
        line = "po::store(po::parse_config_file(confStream, confOptionsDesc, true), confOptions);"
    # Change the default loaded config file
    if "(\"config,c\", po::value<std::string>(), \"configuration file\");" in line:
        line = '("config,c", po::value<std::string>()->default_value("./configs/-.conf"), "configuration file");'
    # sys.stdout is redirected to the file
    sys.stdout.write(line)
    if "RpcNodeConfiguration::initOptions(remoteNodeOptions);" in line:
        sys.stdout.write(ConfigurationManager_cpp_initOptions);
    if "remoteNodeConfig.init(confOptions);" in line:
        sys.stdout.write(ConfigurationManager_cpp_coinBaseConfig_init_confOptions);
# Change this when Bytecoin debugs
#    if "remoteNodeConfig.init(cmdOptions);" in line:
#        sys.stdout.write(ConfigurationManager_cpp_coinBaseConfig_init_cmdOptions);


# Text added to src/payment_service/main.cpp
payment_service_main_currency_params = textwrap.dedent("""\
  currencyBuilder->genesisCoinbaseTxHex(config.coinBaseConfig.GENESIS_COINBASE_TX_HEX);
  currencyBuilder->publicAddressBase58Prefix(config.coinBaseConfig.CRYPTONOTE_PUBLIC_ADDRESS_BASE58_PREFIX);
  currencyBuilder->moneySupply(config.coinBaseConfig.MONEY_SUPPLY);
  currencyBuilder->emissionSpeedFactor(config.coinBaseConfig.EMISSION_SPEED_FACTOR);
  currencyBuilder->blockGrantedFullRewardZone(config.coinBaseConfig.CRYPTONOTE_BLOCK_GRANTED_FULL_REWARD_ZONE);
  currencyBuilder->numberOfDecimalPlaces(config.coinBaseConfig.CRYPTONOTE_DISPLAY_DECIMAL_POINT);
  currencyBuilder->mininumFee(config.coinBaseConfig.MINIMUM_FEE);
  currencyBuilder->defaultDustThreshold(config.coinBaseConfig.DEFAULT_DUST_THRESHOLD);
  currencyBuilder->difficultyTarget(config.coinBaseConfig.DIFFICULTY_TARGET);
  currencyBuilder->minedMoneyUnlockWindow(config.coinBaseConfig.CRYPTONOTE_MINED_MONEY_UNLOCK_WINDOW);
  currencyBuilder->maxBlockSizeInitial(config.coinBaseConfig.MAX_BLOCK_SIZE_INITIAL);

  if (config.coinBaseConfig.EXPECTED_NUMBER_OF_BLOCKS_PER_DAY && config.coinBaseConfig.EXPECTED_NUMBER_OF_BLOCKS_PER_DAY != 0)
  {
    currencyBuilder->difficultyWindow(config.coinBaseConfig.EXPECTED_NUMBER_OF_BLOCKS_PER_DAY);
    currencyBuilder->upgradeVotingWindow(config.coinBaseConfig.EXPECTED_NUMBER_OF_BLOCKS_PER_DAY);
    currencyBuilder->upgradeWindow(config.coinBaseConfig.EXPECTED_NUMBER_OF_BLOCKS_PER_DAY);
  } else {
    currencyBuilder->difficultyWindow(24 * 60 * 60 / config.coinBaseConfig.DIFFICULTY_TARGET);
  }
  currencyBuilder->maxBlockSizeGrowthSpeedDenominator(365 * 24 * 60 * 60 / config.coinBaseConfig.DIFFICULTY_TARGET);
  currencyBuilder->lockedTxAllowedDeltaSeconds(config.coinBaseConfig.DIFFICULTY_TARGET * CryptoNote::parameters::CRYPTONOTE_LOCKED_TX_ALLOWED_DELTA_BLOCKS);

  if (config.coinBaseConfig.UPGRADE_HEIGHT && config.coinBaseConfig.UPGRADE_HEIGHT != 0)
  {
    currencyBuilder->upgradeHeight(config.coinBaseConfig.UPGRADE_HEIGHT);
  }
  currencyBuilder->difficultyLag(config.coinBaseConfig.DIFFICULTY_CUT);
  currencyBuilder->difficultyCut(config.coinBaseConfig.DIFFICULTY_LAG);
""")

# Make changes in src/payment_service/main.cpp
paths['payment_service.main.cpp'] = args.source + "/src/payment_service/main.cpp"
for line in fileinput.input([paths['payment_service.main.cpp']], inplace=True):
    if "CryptoNote::Currency currency = currencyBuilder->currency();" in line:
        sys.stdout.write(payment_service_main_currency_params);
    # sys.stdout is redirected to the file
    sys.stdout.write(line)


# Replace README
paths['README.md'] = args.source + "/README.md"
source_paths['README.md'] = os.path.dirname(os.path.realpath(__file__)) + '/multiply/README.md'
if (os.path.isfile(source_paths['README.md'])):
    shutil.copyfile(source_paths['README.md'],paths['README.md'])
