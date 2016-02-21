minetest.register_chatcommand("dumpnodes", {
	privs = {server = true},
	description = "Dumps all known nodes in a file",
	func = function()
		local f = io.open(minetest.get_modpath("python_minetest") .. "/knownnodes.txt", "w")
		for node in pairs(minetest.registered_nodes) do
			f:write(node)
			f:write('\n')
		end

		f:flush()
		f:close()

		return true, "Nodes dumped in " .. minetest.get_modpath("python_minetest") .. "/knownnodes.txt"
	end
})
