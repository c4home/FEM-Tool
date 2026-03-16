# ============================================================
# NAS Fastener Toolbox - HyperMesh UI
# Button 1: Fastener Group
# Button 2: Tag Create (tag solids per assembly + include file)
# ============================================================


# ══════════════════════════════════════════════════════════════
# PROC 1 — Fastener Group
# ══════════════════════════════════════════════════════════════
proc run_fastener_group {} {
    *createmark comps 1 "all"
    set all_comp_ids [hm_getmark comps 1]
    hm_markclear comps 1

    if {[llength $all_comp_ids] == 0} {
        tk_messageBox -title "Info" \
            -message "No components found in model." -icon info
        return
    }

    array unset base_to_ids
    array set base_to_ids {}

    foreach id $all_comp_ids {
        set full_name [hm_entityinfo name components $id]
        if {![string match -nocase "NAS*" $full_name]} { continue }
        regsub {\.\d+$} $full_name "" base_name
        if {[info exists base_to_ids($base_name)]} {
            lappend base_to_ids($base_name) $id
        } else {
            set base_to_ids($base_name) [list $id]
        }
    }

    set count 0
    foreach base_name [array names base_to_ids] {
        set comp_ids $base_to_ids($base_name)
        *createentity assems name="$base_name"
        set assem_id [hm_latestentityid assems]
        eval *createmark comps 1 $comp_ids
        *assemblyaddmark $assem_id comps 1
        hm_markclear comps 1
        incr count
    }

    hm_redraw

    tk_messageBox -title "Done" \
        -message "Fastener grouping complete.\n$count assemblies created." \
        -icon info
}


# ══════════════════════════════════════════════════════════════
# PROC 2 — Tag Create
# For each NAS assembly:
#   1. Isolate the assembly (display only its components)
#   2. Collect all solids inside those components
#   3. Create one tag per solid, labelled by solid ID
#   4. Create an include file named after the assembly
#   5. Move the tags into that include file
# ══════════════════════════════════════════════════════════════
proc run_tag_create {} {

    *createmark assems 1 "all"
    set all_assem_ids [hm_getmark assems 1]
    hm_markclear assems 1

    if {[llength $all_assem_ids] == 0} {
        tk_messageBox -title "Info" \
            -message "No assemblies found.\nRun 'Fastener Group' first." \
            -icon warning
        return
    }

    # ── Get working directory ────────────────────────────────
    # Try model file directory first, fall back to HM working dir
    set model_path [hm_info currentfile]
    if {$model_path ne "" && $model_path ne "."} {
        set work_dir [file dirname $model_path]
    } else {
        # ✅ Correct option — not TEMPDIR
        set work_dir [hm_info -appinfo CURRENTWORKINGDIR]
    }
    puts "Include files will be created in: $work_dir"

    set tag_count   0
    set assem_count 0

    foreach assem_id $all_assem_ids {

        set assem_name [hm_entityinfo name assems $assem_id]
        if {![string match -nocase "NAS*" $assem_name]} { continue }

        # ── Step 1: Get components ──────────────────────────
        *createmark comps 1 "by assembly" $assem_id
        set comp_ids [hm_getmark comps 1]
        hm_markclear comps 1
        if {[llength $comp_ids] == 0} { continue }

        # ── Step 2: Isolate display ─────────────────────────
        eval *createmark comps 1 $comp_ids
        *displaycollectorsallbymark 1 "isolate only" 1 1

        # ── Step 3: Collect solids ──────────────────────────
        set all_solid_ids {}
        foreach comp_id $comp_ids {
            *createmark solids 1 "by collector" $comp_id
            set s_ids [hm_getmark solids 1]
            hm_markclear solids 1
            foreach sid $s_ids { lappend all_solid_ids $sid }
        }
        hm_markclear comps 1
        if {[llength $all_solid_ids] == 0} { continue }

        # ── Step 4: Create include with full path ───────────
        # Full path = work_dir/NAS1149C0532R.inc
        # Browser short name = NAS1149C0532R.inc  (filename only)
        set inc_fullpath [file join $work_dir "${assem_name}.inc"]

        set ids_before [hm_getincludes]
        *createinclude $inc_fullpath
        set ids_after  [hm_getincludes]

        set inc_id ""
        foreach id $ids_after {
            if {[lsearch $ids_before $id] < 0} {
                set inc_id $id
                break
            }
        }
        if {$inc_id eq ""} {
            puts "WARNING: Could not resolve include ID for $assem_name"
            continue
        }
        puts "Include OK: $inc_fullpath  (id=$inc_id)"

        # ── Step 4.5: Rename the Include file ───────────────
        *updateinclude $inc_id 1 "$assem_name" 1 $inc_fullpath 0 0
        catch { *endnotehistorystate "Renamed Include File to $assem_name" }

        # ── Step 5: Create one tag per solid (label = ID) ───
        set local_tag_ids {}
        foreach solid_id $all_solid_ids {
            *tagcreate solids $solid_id "$solid_id" "" 4
            set tag_id [hm_latestentityid tags]
            lappend local_tag_ids $tag_id
            incr tag_count
        }

        # ── Step 6: Move tags into include ──────────────────
        if {[llength $local_tag_ids] > 0} {
            eval *createmark tags 1 $local_tag_ids
            *movemark tags 1 $inc_id
            hm_markclear tags 1
        }

        incr assem_count
    }

    # ── Restore full display ─────────────────────────────────
    *createmark comps 1 "all"
    *displaycollectorsallbymark 1 "show" 1 1
    hm_markclear comps 1
    hm_redraw

    tk_messageBox -title "Done" \
        -message "Tag creation complete.\n$assem_count assemblies processed.\n$tag_count tags created." \
        -icon info
}


# ══════════════════════════════════════════════════════════════
# PROC 3 — Node Create (centroid of selected solids)
# ══════════════════════════════════════════════════════════════
proc run_node_create {} {
*clearmark solids 1

*createmarkpanel solids 1 "Select solids to create nodes at centroid:"
set solid_list [hm_getmark solids 1]
*clearmark solids 1

if {[llength $solid_list] == 0} {
    puts "No solids selected."
} else {
    set node_count 0

    foreach solid_id $solid_list {
        *createmark solids 1 $solid_id
        set centroids [hm_getcentroid solids 1]

        set x [lindex $centroids 0]
        set y [lindex $centroids 1]
        set z [lindex $centroids 2]

        *createnode $x $y $z 0 0 0
        incr node_count
        *clearmark solids 1
    }

    puts "Successfully created $node_count free node(s) at solid centroids."
    tk_messageBox -title "Done" \
        -message "Created $node_count node(s) at solid centroids." -icon info
}
}

# ══════════════════════════════════════════════════════════════
# PROC 4 — Create CBUSH (Nearest Nodes from List A to List B)
# ══════════════════════════════════════════════════════════════

proc run_create_cbush {} {
    # ── Select Node List A ──
    *clearmark nodes 1
    *createmarkpanel nodes 1 "Select all Nodes A:"
    set nodes_A [hm_getmark nodes 1]
    *clearmark nodes 1
    
    if {[llength $nodes_A] == 0} {
        tk_messageBox -title "Error" -message "No nodes selected for List A." -icon error
        return
    }

    # ── Select Node List B ──
    *createmarkpanel nodes 1 "Select all Nodes B:"
    set nodes_B [hm_getmark nodes 1]
    *clearmark nodes 1
    
    if {[llength $nodes_B] == 0} {
        tk_messageBox -title "Error" -message "No nodes selected for List B." -icon error
        return
    }
    
    # ── Prepare Element Type ──
    # Explicitly set the spring type to CBUSH
    *elementtype spring CBUSH
    
    set cbush_count 0
    
    # Start the history state (allows users to 'Undo' the whole batch at once)
    catch { *startnotehistorystate {Created CBUSH elements} }
    
    # ── Loop through each Node A to find its closest Node B ──
    foreach node_a $nodes_A {
        set shortest_dist 9999999.9
        set nearest_node_b ""
        
        foreach node_b $nodes_B {
            # Skip if they are the exact same node (prevents zero-length spring errors)
            if {$node_a == $node_b} { continue }
            
            # hm_getdistance returns: {total_distance x_dist y_dist z_dist}
            set dist_info [hm_getdistance nodes $node_a $node_b 0]
            set dist [lindex $dist_info 0]
            
            if {$dist < $shortest_dist} {
                set shortest_dist $dist
                set nearest_node_b $node_b
            }
        }
        
        # Create CBUSH if a nearest node was found
        if {$nearest_node_b ne ""} {
            # Use *springos with the standard 0 0 0 0 1 1 0 parameters
            if {![catch {*springos $node_a $nearest_node_b "" 0 0 0 0 1 1 0} err]} {
                incr cbush_count
            } else {
                puts "Failed to create CBUSH between $node_a and $nearest_node_b. Error: $err"
            }
        }
    }
    
    catch { *endnotehistorystate {Created CBUSH elements} }
    
    hm_redraw
    tk_messageBox -title "Success" \
        -message "Created $cbush_count CBUSH elements between nearest nodes!" -icon info
}

# ══════════════════════════════════════════════════════════════
# UI — Build the toolbox window
# ══════════════════════════════════════════════════════════════
proc build_nas_toolbox {} {
    set w .nas_toolbox
    if {[winfo exists $w]} { destroy $w }

    toplevel $w
    wm title    $w "NAS Fastener Toolbox"
    wm resizable $w 0 0
    wm geometry  $w 300x380

    # ── Section: Grouping ──────────────────────────────────
    label $w.lbl_group -text "Grouping" \
        -font {Helvetica 9 bold} -anchor w -fg "#555555"
    pack $w.lbl_group -fill x -padx 14

    button $w.btn_group \
        -text    "Fastener Group" \
        -font    {Helvetica 10 bold} \
        -bg      "#0055a5" -fg "white" \
        -relief  raised -padx 10 -pady 6 -width 24 \
        -command run_fastener_group
    pack $w.btn_group -padx 14 -pady 4

    button $w.btn_tag \
        -text    "Tag Create" \
        -font    {Helvetica 10 bold} \
        -bg      "#006633" -fg "white" \
        -relief  raised -padx 10 -pady 6 -width 24 \
        -command run_tag_create
    pack $w.btn_tag -padx 14 -pady 4

    button $w.btn_node \
    -text "Node Create" \
    -font {Helvetica 10 bold} \
    -bg "#884400" -fg "white" \
    -relief raised -padx 10 -pady 6 -width 24 \
    -command run_node_create
    pack $w.btn_node -padx 14 -pady 4

    frame $w.sep3 -height 2 -bg "#aaaaaa"
    pack  $w.sep3 -fill x -padx 10 -pady 6

    # ── Section: CBUSH ─────────────────────────────────────
    label $w.lbl_tools -text "CBUSH" \
        -font {Helvetica 9 bold} -anchor w -fg "#555555"
    pack $w.lbl_tools -fill x -padx 14

    # ── Button 4: Create CBUSH ──────────────────────────────
    button $w.btn_cbush \
        -text "Create CBUSH (Nearest)" \
        -font {Helvetica 10 bold} \
        -bg "#660066" -fg "white" \
        -relief raised -padx 10 -pady 6 -width 24 \
        -command run_create_cbush
    pack $w.btn_cbush -padx 14 -pady 4
    
    frame $w.sep4 -height 2 -bg "#aaaaaa"
    pack  $w.sep4 -fill x -padx 10 -pady 6

    wm attributes $w -topmost 1
}

# ── Launch ────────────────────────────────────────────────────
build_nas_toolbox