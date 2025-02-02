import logging

from app.docs_process.single_process import SingleProcess
from app.models.docs import Link


class CheckParentLinkProcess(SingleProcess):
    @property
    def process_type(self) -> str:
        return "pre"

    async def execute_single(self, link_obj: Link):
        curr_link = link_obj.prev_link
        while True:
            prev_link = await self.mdb.get_entry_from_col_value(
                column_name="link",
                column_value=curr_link,
                class_type=Link,
            )
            if prev_link is not None:
                new_prev_link = prev_link.link
                break

            curr_link = "/".join(curr_link.split("/")[:-1])
            logging.info(curr_link)

        if new_prev_link != link_obj.prev_link:
            link_obj.prev_link = new_prev_link

        await self.mdb.update_entry(entity=link_obj, update={self.process_name: True})

    async def post_execute_process(self):
        base_link = await self.mdb.get_entry_from_col_value(
            column_name="link",
            column_value=self.group_id if self.group_id[-1] != "/" else self.group_id[:-1],
            class_type=Link,
        )
        await self.mdb.delete_entity(base_link)

    @property
    def process_name(self) -> str:
        return "check_parent"
