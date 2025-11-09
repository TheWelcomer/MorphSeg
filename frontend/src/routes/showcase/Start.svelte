<script>
    let chefs = [["Cynthia", "/assets/Sprite-Cynthia_Chef.gif"], ["Nathan", "/assets/Sprite-Nathan_Chef.gif"], ["Taoran", "/assets/Sprite-Taoran_Chef.gif"], ["Donnie", "/assets/Sprite-Donny_Chef.gif"], ["Alexis", "/assets/Sprite-Alexis_Chef.gif"]];
    
    let started = $state(false) 

    function startCooking() {
        started = true
    }
</script>

<style>
    @import "./style.css";
    #starting-board {
        align-items: center;
        justify-content: center;
        display: flex;
        position: relative;
        background-image: url("/assets/Sprite-cuttingboard.png");
        background-repeat: no-repeat;
        background-size: contain;
        background-position: left center;
        margin: none;
    }
    #startid {
        background-color: transparent;
        height: 100%;
        width: 100%;
        float: left;
        position: fixed;
    }
    .chef {
        image-rendering: pixelated;
        position: absolute;
        width: 6vmax;
        height: 6vmax;
    }
    #declaration {
        text-align: center;
        margin: auto;
        font-size: 10vh;
        color: #b82634;
    }
    #instruction {
        text-align: center;
        margin: auto;
        font-size: 4vh;
        color: #000000;
        animation: 1s linear infinite normal blink;
    }
    @keyframes blink {
        from {
            visibility: visible;
        }
        to {
            visibility: hidden;
        }
    }
</style>

{#if !started}
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div id="starting-board" onclick={startCooking}>
        {#each chefs as chef, order}
            <img class="chef" src={chef[1]} alt={chef[0]} style="left:{35+order*5}vw">
        {/each}
        <div id="declaration">MORPHOLOGICAL SEGMENTATION!</div>
        <div id="instruction">click here to start</div>
    </div>
{/if}
