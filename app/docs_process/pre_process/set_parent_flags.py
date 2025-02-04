from app.docs_process.simple_process import SimpleProcess
from app.models.docs import Link


class SetParentFlags(SimpleProcess):
    async def execute_single(self, link_obj: Link):
        first_link_obj = await self.mdb.get_entry_from_col_value(
            column_name="prev_link",
            column_value=link_obj.link,
            class_type=Link,
        )
        if first_link_obj is not None:
            link_obj.is_parent = True
            await self.mdb.update_entry(link_obj)

        await self.mdb.update_entry(entity=link_obj, update={self.process_name: True})

    @property
    def process_name(self) -> str:
        return "parents"

    @property
    def process_type(self) -> str:
        return "pre"
